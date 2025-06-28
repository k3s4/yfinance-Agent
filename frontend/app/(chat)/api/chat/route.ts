import type { Message } from 'ai';
import {
  deleteChatById,
  getChatById,
  saveChat,
  saveMessages,
} from '@/lib/db/queries';
import {
  generateUUID,
} from '@/lib/utils';

import { generateTitleFromUserMessage } from '../../actions';

export const dynamic = 'force-dynamic';
export const maxDuration = 60;

// バックエンドAPIのベースURL
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  const {
    id,
    messages,
    modelId,
  }: {
    id: string;
    messages: Array<Message>;
    modelId: string;
  } = await request.json();

  // 最新のユーザーメッセージを取得
  const userMessages = messages.filter(m => m.role === 'user');
  if (!userMessages.length) {
    return new Response('No user message found', { status: 400 });
  }

  const userMessage = userMessages[userMessages.length - 1];

  const chat = await getChatById({ id });

  if (!chat) {
    const title = await generateTitleFromUserMessage({ message: userMessage, modelApiKey: 'dummy' });
    await saveChat({ id, title });
  }

  const userMessageId = generateUUID();

  await saveMessages({
    messages: [
      { ...userMessage, id: userMessageId, createdAt: new Date(), chatId: id },
    ],
  });

  try {
    // バックエンドAPIに転送
    const backendResponse = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id,
        messages,
        modelId,
      }),
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text().catch(() => 'Unknown error');
      console.error(`Backend API error: ${backendResponse.status} ${backendResponse.statusText}`, errorText);
      
      let errorMessage = 'バックエンドでエラーが発生しました。';
      switch (backendResponse.status) {
        case 400:
          errorMessage = 'リクエストが正しくありません。入力内容を確認してください。';
          break;
        case 401:
          errorMessage = '認証が必要です。API設定を確認してください。';
          break;
        case 403:
          errorMessage = 'アクセスが拒否されました。権限を確認してください。';
          break;
        case 404:
          errorMessage = 'エンドポイントが見つかりません。バックエンドが起動しているか確認してください。';
          break;
        case 429:
          errorMessage = 'リクエスト回数が上限を超えました。しばらく待ってから再試行してください。';
          break;
        case 500:
          errorMessage = 'サーバー内部エラーが発生しました。';
          break;
        case 502:
        case 503:
        case 504:
          errorMessage = 'サーバーが一時的に利用できません。しばらく待ってから再試行してください。';
          break;
        default:
          errorMessage = `予期しないエラーが発生しました (${backendResponse.status})。`;
      }
      
      throw new Error(errorMessage);
    }

    // ストリーミングレスポンスを転送
    const reader = backendResponse.body?.getReader();
    if (!reader) {
      throw new Error('No response body from backend');
    }

    let assistantContent = '';
    
    const stream = new ReadableStream({
      start(controller) {
        function pump(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              // バックエンドからのレスポンス完了後にアシスタントメッセージを保存
              if (assistantContent.trim()) {
                const assistantMessageId = generateUUID();
                saveMessages({
                  messages: [
                    {
                      id: assistantMessageId,
                      chatId: id,
                      role: 'assistant',
                      content: assistantContent.trim(),
                      createdAt: new Date(),
                    },
                  ],
                }).catch(error => {
                  console.error('Failed to save assistant message:', error);
                });
              }
              controller.close();
              return;
            }
            
            // レスポンス内容を蓄積（text-deltaの場合）
            if (value) {
              const chunk = new TextDecoder().decode(value);
              try {
                const lines = chunk.split('\n');
                for (const line of lines) {
                  if (line.startsWith('data: ') && !line.includes('[DONE]')) {
                    const data = JSON.parse(line.substring(6));
                    // 新しいtextDelta形式と従来のcontent形式の両方をサポート
                    if (data.type === 'text-delta') {
                      const delta = data.textDelta || data.content || '';
                      assistantContent += delta;
                    }
                  }
                }
              } catch (e) {
                // JSON解析エラーは無視（ストリーミング中の不完全なデータ）
                console.warn('Failed to parse streaming data:', e);
              }
            }
            
            controller.enqueue(value);
            return pump();
          });
        }
        return pump();
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error calling backend API:', error);
    
    let errorMessage = 'チャット処理中にエラーが発生しました。';
    let statusCode = 500;
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      errorMessage = 'バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。';
      statusCode = 502;
    } else if (error instanceof Error) {
      errorMessage = error.message;
      // エラーメッセージに基づいてステータスコードを調整
      if (error.message.includes('404') || error.message.includes('エンドポイントが見つかりません')) {
        statusCode = 404;
      } else if (error.message.includes('400') || error.message.includes('リクエストが正しくありません')) {
        statusCode = 400;
      }
    }
    
    return new Response(JSON.stringify({ 
      error: errorMessage,
      timestamp: new Date().toISOString(),
      path: '/api/chat'
    }), { 
      status: statusCode,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    return new Response('Not Found', { status: 404 });
  }

  try {
    // バックエンドにも削除リクエストを送信
    try {
      await fetch(`${BACKEND_URL}/api/chat?chat_id=${id}`, {
        method: 'DELETE',
      });
    } catch (backendError) {
      console.warn('Failed to delete chat from backend:', backendError);
      // バックエンドのエラーは無視してフロントエンドの削除は続行
    }

    await deleteChatById({ id });
    return new Response('Chat deleted', { status: 200 });
  } catch (error) {
    console.error('Error deleting chat:', error);
    
    let errorMessage = 'チャット削除中にエラーが発生しました。';
    if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    return new Response(JSON.stringify({ 
      error: errorMessage,
      timestamp: new Date().toISOString(),
      path: '/api/chat'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}
