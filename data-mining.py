import re

# 1. Fungsi stemming: Confix Stripping (CSS)

def css_stemmer(word):
    """
    Simulasi sederhana algoritma Confix Stripping.
    Menghapus awalan (prefix) dan akhiran (suffix) secara berurutan.
    """
    word = word.lower().strip()

    word = re.sub(r'(kan|an|i)$','',word)

    word = re.sub(r'^(mem|men|meng|me|per|pe|ber|be|di|ter|te|ke|se)', '', word)
    
    return word

#2. Fungsi binary term matching

def binary_matching(query, docs):
    """
    Mencocokkan query terhadap dokumen.
    Jika kata kunci (setelah di-stem) ada di dokumen, beri nilai 1, jika tidak 0.
    """
    # Preprocessing pada Query
    stemmed_query = css_stemmer(query)
    
    print(f"--- ANALISIS SISTEM ---")
    print(f"Query Asli     : {query}")
    print(f"Query Stemmed  : {stemmed_query}\n")
    
    results = []
    
    for i, original_doc in enumerate(docs):
        # Preprocessing pada Dokumen: pecah jadi kata, lalu stem tiap kata
        words_in_doc = original_doc.lower().split()
        stemmed_doc_words = [css_stemmer(w) for w in words_in_doc]
        
        # Binary Matching: Cek apakah kata kunci ada di list kata dokumen
        match_status = 1 if stemmed_query in stemmed_doc_words else 0
        
        results.append({
            "id": i + 1,
            "original": original_doc,
            "stemmed": " ".join(stemmed_doc_words),
            "status": match_status
        })
        
    return results


# 3. DATA & EKSEKUSI (SIMULASI TUGAS)

data_dokumen = [
    "Ibu sedang memasak makanan di dapur",
    "Budi bermain bola di lapangan",
    "Adik memakan roti yang dibeli ibu",
    "Mereka sedang melakukan permainan tradisional",
    "Proses pembelajaran data mining sangat seru"
]

# Input Query dari User
query_user = "makan"  

# Jalankan Sistem
hasil_pencarian = binary_matching(query_user, data_dokumen)

# Tampilkan Hasil dalam Tabel Sederhana
print(f"{'ID':<3} | {'Status':<8} | {'Dokumen Asli'}")
print("-" * 60)
for res in hasil_pencarian:
    status_label = "MATCH (1)" if res['status'] == 1 else "NO (0)"
    print(f"{res['id']:<3} | {status_label:<8} | {res['original']}")

print("\n--- DETAIL STEMMING DOKUMEN ---")
for res in hasil_pencarian:
    print(f"Doc {res['id']} Stemmed: {res['stemmed']}")