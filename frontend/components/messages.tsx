import { ChatRequestOptions, Message } from 'ai';
import { LoadingMessage, PreviewMessage, ThinkingMessage } from './message';
import { useScrollToBottom } from './use-scroll-to-bottom';
import { memo } from 'react';
import equal from 'fast-deep-equal';
import { useQueryLoadingSelector } from '@/hooks/use-query-loading';

interface MessagesProps {
  chatId: string;
  isLoading: boolean;
  messages: Array<Message>;
  setMessages: (
    messages: Message[] | ((messages: Message[]) => Message[]),
  ) => void;
  reload: (
    chatRequestOptions?: ChatRequestOptions,
  ) => Promise<string | null | undefined>;
  isReadonly: boolean;
  isBlockVisible: boolean;
}

function PureMessages({
  chatId,
  isLoading,
  messages,
  setMessages,
  reload,
  isReadonly,
}: MessagesProps) {
  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  const queryLoadingState = useQueryLoadingSelector(state => state);

  const loadingMessages = queryLoadingState.taskNames.length > 0
    ? queryLoadingState.taskNames
    : [];

  return (
    <div
      className="flex flex-col min-w-0 gap-4 flex-1 overflow-y-scroll mt-6"
    >
      {messages.map((message, index) => (
        <PreviewMessage
          key={message.id}
          chatId={chatId}
          message={message}
          isLoading={isLoading && messages.length - 1 === index}
          setMessages={setMessages}
          reload={reload}
          isReadonly={isReadonly}
        />
      ))}

      {(isLoading || queryLoadingState.isLoading) &&
        messages.length > 0 &&
        messages[messages.length - 1].role === 'user' && (
          <ThinkingMessage />
        )}

      {queryLoadingState.isLoading && (
        <LoadingMessage loadingMessages={loadingMessages} />
      )}

      <div
        ref={messagesEndRef}
        className="shrink-0 min-w-[24px] min-h-[24px]"
      />
    </div>
  );
}

export const Messages = memo(PureMessages, (prevProps, nextProps) => {
  if (prevProps.isBlockVisible && nextProps.isBlockVisible) return true;

  if (prevProps.isLoading !== nextProps.isLoading) return false;
  if (prevProps.isLoading && nextProps.isLoading) return false;
  if (prevProps.messages.length !== nextProps.messages.length) return false;

  return true;
});
