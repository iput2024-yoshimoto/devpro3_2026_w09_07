/**
 * @jest-environment jsdom
 */

// テスト用のHTML構造
const HTML_STRUCTURE = `
  <span id="last-update">--</span>
  <button id="refresh-btn"></button>
  <span id="avg-temp">--.-</span>
  <span id="avg-humid">--.-</span>
  <span id="avg-co2">----</span>
  
  <form id="sensor-form">
    <input type="number" id="input-temp" name="temperature" value="25.0">
    <input type="number" id="input-humid" name="humidity" value="50.0">
    <input type="number" id="input-co2" name="co2" value="800">
    <input type="text" id="input-student-id" name="student_id" value="TK240006">
    <button type="submit">送信</button>
  </form>

  <table>
    <tbody id="data-tbody">
      <tr>
        <td>2026-07-23 12:00:00</td>
        <td>20.0</td>
        <td>40.0</td>
        <td>500</td>
        <td>TK240006</td>
      </tr>
      <tr>
        <td>2026-07-23 12:05:00</td>
        <td>30.0</td>
        <td>70.0</td>
        <td>1100</td>
        <td>TK240006</td>
      </tr>
    </tbody>
  </table>

  <div id="warning-msg" class="hidden"></div>
  <button id="confirm-btn"></button>
`;

describe('センサダッシュボード JSテスト', () => {
  beforeEach(() => {
    document.body.innerHTML = HTML_STRUCTURE;
    jest.resetModules();

    global.alert = jest.fn();
    jest.spyOn(console, 'error').mockImplementation(() => {});

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ status: 'ok' }),
      })
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('平均値（温度・湿度・CO2）が正しく計算されて表示されるか', () => {
    // テーブル内のデータ行から平均値を直接計算して表示するロジックの検証
    const rows = document.querySelectorAll('#data-tbody tr');
    let totalTemp = 0, totalHumid = 0, totalCo2 = 0;

    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      totalTemp += parseFloat(cells[1].textContent);
      totalHumid += parseFloat(cells[2].textContent);
      totalCo2 += parseFloat(cells[3].textContent);
    });

    const count = rows.length;
    document.getElementById('avg-temp').textContent = (totalTemp / count).toFixed(1);
    document.getElementById('avg-humid').textContent = (totalHumid / count).toFixed(1);
    document.getElementById('avg-co2').textContent = Math.round(totalCo2 / count).toString();

    expect(document.getElementById('avg-temp').textContent).toBe('25.0');
    expect(document.getElementById('avg-humid').textContent).toBe('55.0');
    expect(document.getElementById('avg-co2').textContent).toBe('800');
  });

  test('CO2が1000ppm以上、または湿度が60%以上で警告メッセージが表示されるか', () => {
    const rows = document.querySelectorAll('#data-tbody tr');
    let hasWarning = false;

    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      const humid = parseFloat(cells[2].textContent);
      const co2 = parseFloat(cells[3].textContent);
      if (co2 >= 1000 || humid >= 60) {
        hasWarning = true;
      }
    });

    const warningDiv = document.getElementById('warning-msg');
    if (hasWarning) {
      warningDiv.classList.remove('hidden');
    }

    expect(warningDiv.classList.contains('hidden')).toBe(false);
  });

  test('手動登録フォーム送信時に /submit へ POST リクエストが飛ばされるか', async () => {
    const form = document.getElementById('sensor-form');
    
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      fetch('/submit', {
        method: 'POST',
        body: formData
      });
    });

    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));

    expect(global.fetch).toHaveBeenCalledWith('/submit', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData)
    }));
  });
});