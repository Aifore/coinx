# /// script
# requires-python = ">=3.11"
# dependencies = ["rumps"]
# ///
import shutil
import threading
from datetime import UTC, datetime

import objc
import rumps
from AppKit import (
    NSBox,
    NSBoxSeparator,
    NSColor,
    NSControlSizeRegular,
    NSFont,
    NSFontAttributeName,
    NSFontWeightRegular,
    NSFontWeightSemibold,
    NSForegroundColorAttributeName,
    NSMutableParagraphStyle,
    NSParagraphStyleAttributeName,
    NSScroller,
    NSScrollerStyleLegacy,
    NSScrollView,
    NSTextAlignmentRight,
    NSTextField,
    NSTextTab,
    NSView,
)
from Foundation import (
    NSAttributedString,
    NSMakeRect,
    NSMaxX,
    NSMutableAttributedString,
    NSUserDefaults,
)
from PyObjCTools.AppHelper import callAfter

from binance_report import (
    ZERO,
    Binance,
    collect,
    contract_summary,
    daily_breakdown,
    overview,
    fmt,
    spot_summary,
    total,
)

REFRESH_MINUTES_OPTIONS = (1, 2, 5, 15, 30, 60)
DEFAULT_REFRESH_MINUTES = 5
REFRESH_MINUTES_KEY = "binancePnlRefreshMinutes"
COLUMN_GAP = 12
ROW_INSET = 12
ROW_PADDING = 4
LINE_HEIGHT = 19
DIVIDER_SPACE = 7
WHEEL_LINE_STEP = 12
# 数据列可见宽度上限，超出部分左右滑动；屏幕右侧仍放不下时调小此值
MAX_SCROLL_WIDTH = 360
FONT = NSFont.monospacedDigitSystemFontOfSize_weight_(12, NSFontWeightRegular)
BOLD_FONT = NSFont.monospacedDigitSystemFontOfSize_weight_(12, NSFontWeightSemibold)

SPOT_COLUMNS = (
    ("币种", "name", "text"),
    ("数量", "quantity", "number"),
    ("现价", "price", "number"),
    ("市值", "value", "money"),
    ("涨幅", "change", "percent"),
    ("今日", "day", "pnl"),
)
OVERVIEW_COLUMNS = (
    ("币种", "name", "text"),
    ("数量", "quantity", "number"),
    ("现价", "price", "number"),
    ("市值", "value", "money"),
    ("占比", "share", "share"),
)
CONTRACT_COLUMNS = (
    ("合约", "name", "text"),
    ("数量", "quantity", "number"),
    ("开仓价", "entry", "number"),
    ("现价", "mark", "number"),
    ("仓位", "notional", "money"),
    ("保证金", "margin", "money"),
    ("浮盈", "pnl", "pnl"),
    ("回报率", "roi", "percent"),
    ("今日", "day", "pnl"),
)


def number(value):
    if value is None:
        return "未取得"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 1 or value == 0:
        return f"{value:,.2f}"
    significant_decimals = 3 - value.adjusted()
    return f"{value:.{significant_decimals}f}"


FORMATTERS = dict(
    text=str,
    number=number,
    money=number,
    pnl=lambda value: fmt(value, signed=True),
    percent=lambda value: "—" if value is None else f"{value:+.1f}%",
    share=lambda value: "—" if value is None else f"{value:.1f}%",
)


def sign_color(value):
    if value is None:
        return NSColor.secondaryLabelColor()
    if value > 0:
        return NSColor.systemGreenColor()
    if value < 0:
        return NSColor.systemRedColor()
    return NSColor.labelColor()


def cells(row, columns):
    result = []
    for _, key, kind in columns:
        if key not in row:
            result.append(("—", NSColor.tertiaryLabelColor()))
            continue
        value = row[key]
        signed = kind in {"pnl", "percent"}
        color = sign_color(value) if signed else NSColor.labelColor()
        unit = row.get(f"{key}_unit", "") if value is not None else ""
        result.append((f"{FORMATTERS[kind](value)}{unit}", color))
    return result


def text_width(text, font=FONT):
    attributes = {NSFontAttributeName: font}
    return (
        NSAttributedString.alloc()
        .initWithString_attributes_(text, attributes)
        .size()
        .width
    )


def tab_stops(widths, start=0):
    # 菜单里没有表格控件：按实测文字宽度设置右对齐制表位，中英文混排也能对齐
    stops, location = [], start
    for width in widths:
        location += width
        stops.append(
            NSTextTab.alloc().initWithTextAlignment_location_options_(
                NSTextAlignmentRight, location, {}
            )
        )
        location += COLUMN_GAP
    return stops


def paragraph_style(stops):
    style = NSMutableParagraphStyle.alloc().init()
    style.setTabStops_(stops)
    # 固定行高：冻结列和滚动列分属两个文本框，中文回退字体行高不同会导致行错位
    style.setMinimumLineHeight_(LINE_HEIGHT)
    style.setMaximumLineHeight_(LINE_HEIGHT)
    return style


def attributed(lines, style, tabbed, divider_after=None):
    """lines 为 [(字体, [(文字, 颜色), ...])]；tabbed 时每格前加制表符跳到右对齐列。"""
    divider_style = style.mutableCopy()
    divider_style.setParagraphSpacing_(DIVIDER_SPACE)
    result = NSMutableAttributedString.alloc().init()
    for index, (font, line_cells) in enumerate(lines):
        for text, color in line_cells:
            attributes = {
                NSFontAttributeName: font,
                NSForegroundColorAttributeName: color,
                NSParagraphStyleAttributeName: (
                    divider_style if index == divider_after else style
                ),
            }
            prefix = "\t" if tabbed else ""
            result.appendAttributedString_(
                NSAttributedString.alloc().initWithString_attributes_(
                    f"{prefix}{text}", attributes
                )
            )
        if index < len(lines) - 1:
            result.appendAttributedString_(
                NSAttributedString.alloc().initWithString_("\n")
            )
    return result


def fitted_label(text):
    label = NSTextField.labelWithAttributedString_(text)
    label.sizeToFit()
    return label


class TopAlignedView(NSView):
    # 翻转坐标后，滚动区比数据高时数据贴顶，与左侧冻结列逐行对齐
    def isFlipped(self):
        return True


class HorizontalScrollView(NSScrollView):
    # 鼠标滚轮只有纵向位移，表格只能横向滚动，换算成横向才能用滚轮翻看右侧列
    def scrollWheel_(self, event):
        delta_x, delta_y = event.scrollingDeltaX(), event.scrollingDeltaY()
        if abs(delta_y) <= abs(delta_x):
            return objc.super(HorizontalScrollView, self).scrollWheel_(event)
        step = 1 if event.hasPreciseScrollingDeltas() else WHEEL_LINE_STEP
        clip = self.contentView()
        bounds = clip.bounds()
        moved = ((bounds.origin.x - delta_y * step, bounds.origin.y), bounds.size)
        clip.scrollToPoint_(clip.constrainBoundsRect_(moved).origin)
        self.reflectScrolledClipView_(clip)


def table_view(lines, divider_after):
    """首列冻结在左侧，其余列放进可横向滚动的区域。"""
    names = fitted_label(
        attributed(
            [(font, row[:1]) for font, row in lines],
            paragraph_style([]),
            False,
            divider_after,
        )
    )
    values = [(font, row[1:]) for font, row in lines]
    widths = [
        max(text_width(text, font) for font, (text, _) in column)
        for column in zip(*([(font, cell) for cell in row] for font, row in values))
    ]
    data = fitted_label(
        attributed(values, paragraph_style(tab_stops(widths)), True, divider_after)
    )

    content = data.frame().size
    scrollable = content.width > MAX_SCROLL_WIDTH
    # 按常驻滚动条的高度在底部留位：接鼠标时系统用常驻样式，会占用高度挤压数据；
    # 触控板的悬浮样式则正好落在这段空白上，不会盖住最后一行
    scroller_space = (
        NSScroller.scrollerWidthForControlSize_scrollerStyle_(
            NSControlSizeRegular, NSScrollerStyleLegacy
        )
        if scrollable
        else 0
    )
    scroll_height = content.height + scroller_space
    scroll = HorizontalScrollView.alloc().initWithFrame_(
        NSMakeRect(
            ROW_INSET + names.frame().size.width + COLUMN_GAP,
            ROW_PADDING,
            min(content.width, MAX_SCROLL_WIDTH),
            scroll_height,
        )
    )
    scroll.setDrawsBackground_(False)
    scroll.setHasHorizontalScroller_(scrollable)
    document = TopAlignedView.alloc().initWithFrame_(
        NSMakeRect(0, 0, content.width, content.height)
    )
    data.setFrameOrigin_((0, 0))
    document.addSubview_(data)
    scroll.setDocumentView_(document)

    height = scroll_height + ROW_PADDING * 2
    names.setFrameOrigin_((ROW_INSET, height - ROW_PADDING - names.frame().size.height))
    width = NSMaxX(scroll.frame()) + ROW_INSET
    # 让分隔线落在“合计行基线”与“下一行大写字母顶部”正中：
    # 固定行高多出的行距在文字上方，数字又没有下伸部分，按行框居中会偏上
    leading_above = LINE_HEIGHT - (FONT.ascender() - FONT.descender())
    space_below = leading_above + FONT.ascender() - FONT.capHeight()
    space_above = -FONT.descender()
    divider_y = (
        height
        - ROW_PADDING
        - LINE_HEIGHT * (divider_after + 1)
        - DIVIDER_SPACE / 2
        - (space_below - space_above) / 2
    )
    divider = NSBox.alloc().initWithFrame_(
        NSMakeRect(ROW_INSET, divider_y, width - ROW_INSET * 2, 1)
    )
    divider.setBoxType_(NSBoxSeparator)
    view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
    view.addSubview_(names)
    view.addSubview_(scroll)
    view.addSubview_(divider)
    return view


def table_item(rows, summary, columns, size_key):
    header = [(title, NSColor.secondaryLabelColor()) for title, _, _ in columns]
    # 没有该字段的行（如币本位抵押、查询失败的占位行）不是持仓，排在最后
    ordered = sorted(rows, key=lambda row: row.get(size_key) or ZERO, reverse=True)
    lines = [
        (FONT, header),
        (BOLD_FONT, cells(summary, columns)),
        *((FONT, cells(row, columns)) for row in ordered),
    ]
    item = rumps.MenuItem(f"{columns[0][0]}明细", callback=lambda _: None)
    item._menuitem.setView_(table_view(lines, divider_after=1))
    return item


def parent_items(groups):
    labels = [(label, NSColor.labelColor()) for label, _ in groups]
    days = [cells(summary, (("", "day", "pnl"),)) for _, summary in groups]
    name_width = max(text_width(text) for text, _ in labels)
    style = paragraph_style(
        tab_stops(
            [max(text_width(text) for ((text, _),) in days)], name_width + COLUMN_GAP
        )
    )
    items = []
    for label, day in zip(labels, days):
        item = rumps.MenuItem(label[0])
        tabbed_day = [(f"\t{text}", color) for text, color in day]
        title = attributed([(FONT, [label, *tabbed_day])], style, False)
        item._menuitem.setAttributedTitle_(title)
        items.append(item)
    return items


def headline(*summaries):
    values = [summary["day"] for summary in summaries]
    known = total(value for value in values if value is not None)
    suffix = " ⚠" if None in values else ""
    return f"₿ {fmt(known, signed=True)}{suffix}"


class PnlApp(rumps.App):
    def __init__(self, client):
        super().__init__("币安今日盈亏", title="₿ …", quit_button=None)
        self.client = client
        self.loading = False
        self.defaults = NSUserDefaults.standardUserDefaults()
        saved_minutes = self.defaults.integerForKey_(REFRESH_MINUTES_KEY)
        self.refresh_minutes = (
            saved_minutes
            if saved_minutes in REFRESH_MINUTES_OPTIONS
            else DEFAULT_REFRESH_MINUTES
        )
        self.timer = None
        self.start_timer()

    def start_timer(self):
        # rumps 的 Timer 启动即触发一次，切换频率后会立即刷新并按新间隔重建菜单
        if self.timer:
            self.timer.stop()
        self.timer = rumps.Timer(self.refresh, self.refresh_minutes * 60)
        self.timer.start()

    def set_refresh_minutes(self, minutes):
        self.refresh_minutes = minutes
        self.defaults.setInteger_forKey_(minutes, REFRESH_MINUTES_KEY)
        self.start_timer()

    def frequency_menu(self):
        parent = rumps.MenuItem(f"刷新频率：{self.refresh_minutes} 分钟")
        for minutes in REFRESH_MINUTES_OPTIONS:
            item = rumps.MenuItem(
                f"{minutes} 分钟",
                callback=lambda _, minutes=minutes: self.set_refresh_minutes(minutes),
            )
            item.state = int(minutes == self.refresh_minutes)
            parent.add(item)
        return parent

    def refresh(self, _=None):
        if self.loading:
            return
        self.loading = True
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        try:
            warnings = []
            data, market = collect(self.client, datetime.now(UTC), warnings)
            result = (*daily_breakdown(data, market), *overview(data, market), warnings)
        except Exception as error:  # 后台线程异常若不兜住，菜单栏会永远停在加载中
            result = error
        callAfter(self.show, result)

    def show(self, result):
        self.loading = False
        # 有保存名系统才会记住 ⌘ 拖动后的图标位置；状态栏图标在 run() 之后才创建
        self._nsapp.nsstatusitem.setAutosaveName_("binance-pnl")
        self.menu.clear()
        if isinstance(result, Exception):
            self.title = "₿ ⚠"
            items = [rumps.MenuItem(f"查询失败：{type(result).__name__}")]
        else:
            items = self.report_items(*result)
        self.menu = [
            *items,
            rumps.separator,
            self.frequency_menu(),
            rumps.MenuItem("立即刷新", callback=self.refresh, key="r"),
            rumps.MenuItem("退出", callback=rumps.quit_application, key="q"),
        ]

    def report_items(
        self, spot, contract, funding, overview_rows, overview_summary, warnings
    ):
        detail_groups = (
            ("现货", spot, spot_summary(spot), SPOT_COLUMNS, "value"),
            (
                "合约",
                contract,
                contract_summary(contract, funding),
                CONTRACT_COLUMNS,
                "notional",
            ),
        )
        summaries = [summary for _, _, summary, _, _ in detail_groups]
        self.title = headline(*summaries)
        overview_group = (
            "总览",
            overview_rows,
            dict(overview_summary, day=total(summary["day"] for summary in summaries)),
            OVERVIEW_COLUMNS,
            "value",
        )
        groups = (overview_group, *detail_groups)
        parents = parent_items([(label, summary) for label, _, summary, _, _ in groups])
        for parent, (_, rows, summary, columns, size_key) in zip(parents, groups):
            parent.add(table_item(rows, summary, columns, size_key))
        items = [
            *parents,
            rumps.separator,
            rumps.MenuItem(f"更新于 {datetime.now():%H:%M:%S}（UTC 0 点起算）"),
        ]
        if warnings:
            gaps = rumps.MenuItem(f"数据缺口 {len(warnings)} 项")
            for warning in warnings:
                gaps.add(rumps.MenuItem(warning, callback=lambda _: None))
            items.append(gaps)
        return items


def main():
    executable = shutil.which("binance-cli")
    if not executable:
        raise SystemExit("未找到 binance-cli，请先安装并激活只读 profile。")
    PnlApp(Binance(executable)).run()


if __name__ == "__main__":
    main()
