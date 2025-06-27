import { type Message } from 'ai';
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
      throw new Error(`Backend API error: ${backendResponse.status}`);
    }

    // ストリーミングレスポンスを転送
    const reader = backendResponse.body?.getReader();
    if (!reader) {
      throw new Error('No response body from backend');
    }

    const stream = new ReadableStream({
      start(controller) {
        function pump(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              // バックエンドからのレスポンス完了後にアシスタントメッセージを保存
              // Note: 実際の実装では、レスポンスの内容を取得して保存する必要がある
              controller.close();
              return;
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
    return new Response('Internal Server Error', { status: 500 });
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
    return new Response('An error occurred while processing your request', {
      status: 500,
    });
  }
}
