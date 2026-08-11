import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';
import styles from './ChatMessage.module.css';

interface ChatMessageProps {
  role: 'user' | 'ai';
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={`${styles.messageWrapper} ${isUser ? styles.userWrapper : styles.aiWrapper}`}>
      {!isUser && <div className={styles.avatar} style={{background: 'transparent'}}><Image src="/icon.svg" alt="AI" width={32} height={32} /></div>}
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.aiBubble}`}>
        {isUser ? (
          <p>{content}</p>
        ) : (
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({node, ...props}) => <p style={{margin: '0 0 10px 0'}} {...props} />,
              a: ({node, ...props}) => <a style={{color: 'var(--primary-color)', textDecoration: 'underline'}} target="_blank" rel="noopener noreferrer" {...props} />,
              ul: ({node, ...props}) => <ul style={{margin: '10px 0', paddingLeft: '20px'}} {...props} />,
              ol: ({node, ...props}) => <ol style={{margin: '10px 0', paddingLeft: '20px'}} {...props} />,
              li: ({node, ...props}) => <li style={{marginBottom: '5px'}} {...props} />,
              pre: ({node, ...props}) => (
                <pre style={{
                  background: '#1e1e1e', 
                  color: '#d4d4d4', 
                  padding: '12px', 
                  borderRadius: '8px',
                  overflowX: 'auto',
                  margin: '10px 0'
                }} {...props} />
              ),
              code: ({node, className, children, ...props}: any) => {
                const isInline = !className || !className.includes('language-');
                if (isInline) {
                  return (
                    <code style={{
                      background: 'rgba(0,0,0,0.1)',
                      padding: '2px 4px',
                      borderRadius: '4px',
                      fontFamily: 'monospace'
                    }} className={className} {...props}>
                      {children}
                    </code>
                  )
                }
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>
      {isUser && <div className={styles.avatar} style={{background: 'transparent'}}><Image src="/student-icon.svg" alt="User" width={32} height={32} /></div>}
    </div>
  );
}
