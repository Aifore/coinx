(function () {
    const chart = document.getElementById('{plot_id}');
    function utcMillis(value) {
        if (typeof value === 'number') return value;
        let text = String(value).replace(' ', 'T');
        if (text.length === 10) text += 'T00:00:00';
        if (!/(Z|[+-]\d{2}:\d{2})$/i.test(text)) text += 'Z';
        return Date.parse(text);
    }
    const points = chart.data[0].x.map((value, i) => [utcMillis(value), Number(chart.data[0].y[i])])
        .filter(([time, price]) => Number.isFinite(time) && Number.isFinite(price));

    function fitPrice(range) {
        if (!points.length || !range) return;
        const [start, end] = range.map(utcMillis).sort((a, b) => a - b);
        if (!Number.isFinite(start) || !Number.isFinite(end)) return;
        const values = [];
        for (let i = 0; i < points.length; i++) {
            const [time, price] = points[i];
            if (time >= start && time <= end) values.push(price);
            if (!i) continue;
            const [previousTime, previousPrice] = points[i - 1];
            for (const edge of [start, end]) {
                if (previousTime < edge && edge < time) {
                    values.push(previousPrice + (price - previousPrice) * (edge - previousTime) / (time - previousTime));
                }
            }
        }
        if (!values.length) return;
        const low = Math.min(...values);
        const high = Math.max(...values);
        const padding = Math.max((high - low) * 0.08, Math.abs(high) * 0.002, 0.01);
        return Plotly.relayout(chart, {
            'yaxis.range': [Math.max(0, low - padding), high + padding],
            'yaxis.autorange': false,
        });
    }

    chart.on('plotly_relayout', update => {
        for (const axis of ['xaxis2', 'xaxis']) {
            if (update[`${axis}.autorange`] === true) {
                return fitPrice([points[0]?.[0], points.at(-1)?.[0]]);
            }
            if (update[`${axis}.range`] || `${axis}.range[0]` in update || `${axis}.range[1]` in update) {
                const current = chart.layout[axis].range;
                return fitPrice(update[`${axis}.range`] || [
                    update[`${axis}.range[0]`] ?? current[0],
                    update[`${axis}.range[1]`] ?? current[1],
                ]);
            }
        }
    });
    fitPrice(chart.layout.xaxis.range || chart.layout.xaxis2.range || [points[0]?.[0], points.at(-1)?.[0]]);
})();
