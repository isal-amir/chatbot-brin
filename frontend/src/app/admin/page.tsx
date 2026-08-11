'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import styles from './admin.module.css';

interface Document {
  id: number;
  title: string;
  filename: string;
  created_at: string;
}

interface Student {
  id: number;
  username: string;
}

export default function AdminPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showToast, setShowToast] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Check if user is admin
    const isAdmin = localStorage.getItem('isAdmin');
    if (isAdmin !== 'true') {
      router.push('/chat');
      return;
    }
    fetchDocuments();
    fetchStudents();
  }, [router]);

  const fetchStudents = async () => {
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/admin/students`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStudents(data);
      }
    } catch (err) {
      console.error("Failed to fetch students", err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/admin/documents`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    if (file.type !== 'application/pdf') {
      alert("Hanya file PDF yang diperbolehkan!");
      return;
    }

    setIsUploading(true);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/admin/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.ok) {
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
        fetchDocuments();
      } else {
        const err = await response.json();
        alert(`Gagal menambahkan PDF: ${err.detail}`);
        setProgress(0);
      }
    } catch (err) {
      clearInterval(progressInterval);
      alert("Terjadi kesalahan sistem saat upload.");
      setProgress(0);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteDocument = async (id: number) => {
    if (!confirm("Apakah Anda yakin ingin menghapus PDF ini?")) return;
    
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/admin/documents/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        fetchDocuments();
      } else {
        alert("Gagal menghapus dokumen.");
      }
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  const handleDeleteStudent = async (id: number) => {
    if (!confirm("Apakah Anda yakin ingin menghapus akun siswa ini? Semua riwayat chat akan hilang.")) return;
    
    try {
      const hostname = window.location.hostname;
      const token = localStorage.getItem('token');
      const port = process.env.NODE_ENV === 'production' ? '' : ':8000';
      const response = await fetch(`http://${hostname}${port}/admin/students/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        fetchStudents();
      } else {
        alert("Gagal menghapus siswa.");
      }
    } catch (err) {
      console.error("Failed to delete student", err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('isAdmin');
    router.push('/login');
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Panel Admin 🛡️</h1>
        <button onClick={handleLogout} className={styles.logoutBtn}>Keluar</button>
      </header>

      <main className={styles.mainCard}>
        <section className={styles.uploadSection}>
          <input 
            type="file" 
            accept="application/pdf"
            ref={fileInputRef}
            className={styles.fileInput}
            onChange={handleFileChange}
          />
          <button 
            className={styles.uploadBtn}
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? 'Menambahkan...' : 'Tambahkan Pengetahuan (PDF)'}
          </button>
          
          {isUploading && (
            <div className={styles.progressContainer}>
              <div 
                className={styles.progressBar} 
                style={{ width: `${progress}%` }}
              ></div>
              <div className={styles.progressText}>Memproses dokumen... {progress}%</div>
            </div>
          )}
        </section>

        <section className={styles.docsSection}>
          <h2>Daftar Dokumen PDF</h2>
          {documents.length === 0 ? (
            <div className={styles.noDocs}>Belum ada PDF yang ditambahkan.</div>
          ) : (
            <div className={styles.docList}>
              {documents.map((doc) => (
                <div key={doc.id} className={styles.docItem}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <span className={styles.docIcon}>📄</span>
                    <span className={styles.docTitle}>{doc.title}</span>
                  </div>
                  <button className={styles.deleteBtn} onClick={() => handleDeleteDocument(doc.id)} title="Hapus Dokumen">🗑️</button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className={styles.docsSection} style={{marginTop: '40px'}}>
          <h2>Daftar Akun Siswa</h2>
          {students.length === 0 ? (
            <div className={styles.noDocs}>Belum ada siswa yang terdaftar.</div>
          ) : (
            <div className={styles.docList}>
              {students.map((student) => (
                <div key={student.id} className={styles.docItem}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <span className={styles.docIcon}>🧑‍🎓</span>
                    <span className={styles.docTitle}>{student.username}</span>
                  </div>
                  <button className={styles.deleteBtn} onClick={() => handleDeleteStudent(student.id)} title="Hapus Siswa">🗑️</button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {showToast && (
        <div className={styles.toast}>
          ✅ Penambahan PDF berhasil!
        </div>
      )}
    </div>
  );
}
