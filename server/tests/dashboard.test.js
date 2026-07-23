/**
 * @jest-environment jsdom
 */

// テスト用のHTML構造（HTML_iteration_g7.html の主要DOMを再現）
const HTML_STRUCTURE = `
  <span id="last-update">--</span>
  <button id="refresh-btn"></button>
  <span id="avg-temp">--.-</span>
  <span id="avg-humid">--.-</span>
  <span id="avg-co2">----</span>
  
  <form id="sensor-form">
    <input type="number" id="input-temp" value="25.0">
    <input type="number" id="input-humid" value="50.0">
    <input type="number" id="input-co2" value="800">
    <input type="text" id="input-student-id" value="TK240006">
    <button type="submit">送信</button>
  </form>

  <tbody id="data-tbody">
    <tr class="data-row">
      <td class="temp-cell">20.0</td>
      <td class="humid-cell">40.0</td>
      <td class="co2-cell">500</td>
    </tr>
    <tr class="data-row">
      <td class="temp-cell">30.0</td>
      <td class="humid-cell">70.0</td>
      <td class="co2-cell">1100</td>
    </tr>
  </tbody>

  <div id="warning-msg" class="hidden"></div>
  <button id="confirm-btn"></button>
`;

describe('センサダッシュボード JSテスト', () => {
  beforeEach(() => {
    // DOMの初期化
    document.body.innerHTML = HTML_STRUCTURE;

    // モジュールキャッシュのクリア（毎回新たにJSを読み込み直せるようにする）
    jest.resetModules();

    // alert のモック化
    global.alert = jest.fn();

    // location.reload の安全なモック化
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { reload: jest.fn() }
    });

    // fetch のモック化
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      })
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('平均値（温度・湿度・CO2）が正しく計算されて表示されるか', () => {
    require('../src/static/Java_iteration_g7.js');
    window.dispatchEvent(new Event('DOMContentLoaded'));

    expect(document.getElementById('avg-temp').textContent).toBe('25.0');
    expect(document.getElementById('avg-humid').textContent).toBe('55.0');
    expect(document.getElementById('avg-co2').textContent).toBe('800');
  });

  test('CO2が1000ppm以上、または湿度が60%以上で警告メッセージが表示されるか', () => {
    require('../src/static/Java_iteration_g7.js');
    window.dispatchEvent(new Event('DOMContentLoaded'));

    const warningDiv = document.getElementById('warning-msg');
    expect(warningDiv.classList.contains('hidden')).toBe(false);
    expect(global.alert).toHaveBeenCalledWith('環境が悪化しています。換気を行ってください。');
  });

  test('手動登録フォーム送信時に /submit へ POST リクエストが飛ばされるか', async () => {
    require('../src/static/Java_iteration_g7.js');
    window.dispatchEvent(new Event('DOMContentLoaded'));

    const form = document.getElementById('sensor-form');
    form.dispatchEvent(new Event('submit'));

    expect(global.fetch).toHaveBeenCalledWith('/submit', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData)
    }));
  });
});