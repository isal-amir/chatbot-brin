import React from 'react';
import styles from './TypingIndicator.module.css';

import Image from 'next/image';

export default function TypingIndicator() {
  return (
    <div className={styles.wrapper}>
      <div className={styles.avatar} style={{background: 'transparent'}}>
        <Image src="/icon.svg" alt="AI" width={32} height={32} />
      </div>
      <div className={styles.bubble}>
        <div className={styles.dot}></div>
        <div className={styles.dot}></div>
        <div className={styles.dot}></div>
      </div>
    </div>
  );
}
