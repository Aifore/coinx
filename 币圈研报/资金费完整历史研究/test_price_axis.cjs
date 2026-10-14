const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const updates = [];
let onRelayout;
const chart = {
    data: [{x: ['2025-01-01T00:00:00Z', '2025-01-02T00:00:00Z', '2025-01-03T00:00:00Z'], y: [100, 200, 1000]}],
    layout: {xaxis: {range: ['2025-01-01', '2025-01-03']}, xaxis2: {range: ['2025-01-01', '2025-01-03']}},
    on: (_, callback) => { onRelayout = callback; },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'price_axis.js'), 'utf8'), {
    document: {getElementById: () => chart},
    Plotly: {relayout: (_, update) => {
        updates.push(JSON.parse(JSON.stringify(update)));
        onRelayout(update);
        return Promise.resolve();
    }},
});
assert.deepEqual(updates.at(-1)['yaxis.range'], [28, 1072]);
onRelayout({'xaxis.range': ['2025-01-01', '2025-01-02']});
assert.deepEqual(updates.at(-1)['yaxis.range'], [92, 208]);
onRelayout({'xaxis2.range[0]': '2025-01-02 00:00:00', 'xaxis2.range[1]': '2025-01-03 00:00:00'});
assert.deepEqual(updates.at(-1)['yaxis.range'], [136, 1064]);
onRelayout({'xaxis.range': ['2025-01-01 06:00:00', '2025-01-01 18:00:00']});
assert.deepEqual(updates.at(-1)['yaxis.range'], [121, 179]);
onRelayout({'xaxis.range': ['2025-01-02', '2025-01-02']});
assert.deepEqual(updates.at(-1)['yaxis.range'], [199.6, 200.4]);
const beforeEmpty = updates.length;
onRelayout({'xaxis.range': ['2024-01-01', '2024-01-02']});
assert.equal(updates.length, beforeEmpty);
onRelayout({'xaxis2.autorange': true});
assert.deepEqual(updates.at(-1)['yaxis.range'], [28, 1072]);
assert.ok(updates.every(update => Object.keys(update).every(key => key.startsWith('yaxis.'))));
console.log('价格纵轴检查通过：阶段切换、滑块、局部线段、单点、无数据、复位及递归防护。');
