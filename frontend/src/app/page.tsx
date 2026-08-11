import Link from 'next/link';
import Image from 'next/image';
import styles from './landing.module.css';

export default function LandingPage() {
  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <div className={styles.heroSection}>
          <div className={styles.iconContainer}>
            <Image src="/front-page.svg" alt="AI Icon" width={120} height={120} />
          </div>
          <h1 className={styles.title}>Hermeneutic AI Tutor</h1>
          <h2 className={styles.subtitle}>
            Belajar melalui refleksi dan pemahaman yang mendalam.
          </h2>
          <p className={styles.description}>
            Chatbot ini dirancang untuk tidak sekadar memberikan jawaban instan,
            melainkan membimbingmu untuk berpikir, menganalisis, dan menemukan solusi
            sendiri melalui metode hermeneutika.
          </p>

          <div className={styles.actionContainer}>
            <Link href="/login" className={styles.primaryButton}>
              Mulai Belajar Sekarang 🚀
            </Link>
          </div>
        </div>

        <div className={styles.featuresSection}>
          <div className={styles.featureCard}>
            <h3>💡 Pemahaman Konsep</h3>
            <p>Membantu memahami konsep dasar mikrokontroler dan elektronika secara bertahap.</p>
          </div>
          <div className={styles.featureCard}>
            <h3>🧩 Problem Solving</h3>
            <p>Membimbingmu menemukan kesalahan pada rangkaian atau kodemu sendiri.</p>
          </div>
          <div className={styles.featureCard}>
            <h3>🧠 Berpikir Kritis</h3>
            <p>Dilatih untuk memberikan pertanyaan pancingan, bukan jawaban langsung.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
