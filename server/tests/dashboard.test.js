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
    // DOMの初期化
    document.body.innerHTML = HTML_STRUCTURE;
    jest.resetModules();

    // alert のモック化
    global.alert = jest.fn();

    // console.error（jsdomのnavigation警告）をテスト中だけ一時的に非表示にする
    jest.spyOn(console, 'error').mockImplementation(() => {});

    // fetch のモック化
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
    // JSの読み込みと実行
    require('../src/static/Java_iteration_g7.js');
    document.dispatchEvent(new Event('DOMContentLoaded'));

    expect(document.getElementById('avg-temp').textContent).toBe('25.0');
    expect(document.getElementById('avg-humid').textContent).toBe('55.0');
    expect(document.getElementById('avg-co2').textContent).toBe('800');
  });

  test('CO2が1000ppm以上、または湿度が60%以上で警告メッセージが表示されるか', () => {
    require('../src/static/Java_iteration_g7.js');
    document.dispatchEvent(new Event('DOMContentLoaded'));

    const warningDiv = document.getElementById('warning-msg');
    expect(warningDiv.classList.contains('hidden')).toBe(false);
  });

  test('手動登録フォーム送信時に /submit へ POST リクエストが飛ばされるか', async () => {
    require('../src/static/Java_iteration_g7.js');
    document.dispatchEvent(new Event('DOMContentLoaded'));

    const form = document.getElementById('sensor-form');
    form.dispatchEvent(new Event('submit'));

    expect(global.fetch).toHaveBeenCalledWith('/submit', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData)
    }));
  });
});