window.addEventListener('DOMContentLoaded', () => {
    // 1. 日時表示とリロード処理
    document.getElementById('last-update').textContent = new Date().toLocaleString('ja-JP');
    document.getElementById('refresh-btn').onclick = () => location.reload();

    // 2. データの自動集計と並び替え
    const rows = document.querySelectorAll('.data-row');
    if (rows.length > 0) {
        let tSum = 0, hSum = 0, cSum = 0, vCnt = 0, cCnt = 0;

        rows.forEach(r => {
            const t = parseFloat(r.querySelector('.temp-cell').textContent);
            const h = parseFloat(r.querySelector('.humid-cell').textContent);
            const c = parseFloat(r.querySelector('.co2-cell').textContent);

            if (!isNaN(t) && !isNaN(h)) { tSum += t; hSum += h; vCnt++; }
            if (!isNaN(c)) { cSum += c; cCnt++; }
        });

        if (vCnt > 0) {
            document.getElementById('avg-temp').textContent = (tSum / vCnt).toFixed(1);
            document.getElementById('avg-humid').textContent = (hSum / vCnt).toFixed(1);
        }
        if (cCnt > 0) document.getElementById('avg-co2').textContent = (cSum / cCnt).toFixed(0);

        // 表示順を反転（最新を一番上に）
        const tbody = document.getElementById('data-tbody');
        Array.from(rows).reverse().forEach(r => tbody.appendChild(r));

        // 警告判定
        const lastH = parseFloat(rows[rows.length - 1].querySelector('.humid-cell').textContent);
        const lastC = parseFloat(rows[rows.length - 1].querySelector('.co2-cell').textContent);
        
        if (lastC >= 1000 || lastH >= 60) {
            document.getElementById('warning-msg').classList.remove('hidden');
            alert('環境が悪化しています。換気を行ってください。');
        } else {
            alert('最新データの取得が完了しました');
        }
    }

    // 3. 確認ボタンの処理
    document.getElementById('confirm-btn').onclick = () => alert('確認状態を保存しました。');

    // 4. データ手入力・サーバー送信処理（FormData形式）
    document.getElementById('sensor-form').onsubmit = (e) => {
        e.preventDefault();
        
        // Flaskが受け取りやすい標準フォームデータを作成
        const formData = new FormData();
        formData.append('temperature', document.getElementById('input-temp').value);
        formData.append('humidity', document.getElementById('input-humid').value);
        formData.append('co2', document.getElementById('input-co2').value);
        formData.append('student_id', document.getElementById('input-student-id').value);

        // Python(Flask)側のパス「/submit」に向けて送信
        fetch('/submit', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (res.ok) {
                alert('データを送信しました！');
                document.getElementById('sensor-form').reset(); // 入力欄をクリア
                location.reload(); // 画面をリロードして一覧に反映
            } else {
                alert('送信エラーが発生しました。ステータス: ' + res.status);
            }
        })
        .catch(() => alert('通信エラーが発生しました。'));
    };
});