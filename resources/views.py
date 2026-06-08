from django.db.models import F
from django.views.generic import TemplateView, DetailView

from .models import PsychoArticle, PsychoScale, PsychoVideo, PsychoPodcast, Clinic, ArticleView

COUNTIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
]


class ResourcesView(TemplateView):
    """心理資源頁（訪客可看，無需登入）。"""
    template_name = "resources.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sort = self.request.GET.get("sort", "newest")
        order = "-view_count" if sort == "popular" else "-created_at"
        ctx["articles"] = PsychoArticle.objects.filter(
            is_active=True
        ).exclude(category__in=["AI 小說", "逐字稿"]).order_by(order)
        ctx["current_sort"] = sort
        # 心理科普的分類清單（供 chips 篩選）
        ctx["article_categories"] = [
            (val, label) for val, label in PsychoArticle.CATEGORY_CHOICES
            if val not in ("AI 小說", "逐字稿")
        ]
        ctx["novels"]      = PsychoArticle.objects.filter(is_active=True, category="AI 小說").order_by("-created_at")
        ctx["transcripts"] = PsychoArticle.objects.filter(is_active=True, category="逐字稿").order_by("-created_at")
        ctx["scales"] = PsychoScale.objects.filter(is_active=True)
        ctx["videos"] = PsychoVideo.objects.filter(is_active=True)
        ctx["podcasts"] = PsychoPodcast.objects.filter(is_active=True)
        return ctx


class ArticleDetailView(DetailView):
    """文章詳頁（訪客可看，登入用戶自動記錄閱讀）。"""
    model = PsychoArticle
    template_name = "article_detail.html"
    context_object_name = "article"
    queryset = PsychoArticle.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # 每次開啟都遞增點擊數（F() 原子操作，避免 race condition）
        PsychoArticle.objects.filter(pk=self.object.pk).update(
            view_count=F("view_count") + 1
        )
        # 登入用戶記錄「誰讀了哪篇」（每人每篇只記一次）
        if request.user.is_authenticated:
            ArticleView.objects.get_or_create(
                user=request.user,
                article=self.object,
            )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 所有分類（供篩選 chips 用）
        ctx["all_categories"] = list(
            PsychoArticle.CATEGORY_CHOICES
        )
        # 預設顯示同分類文章
        ctx["filter_category"] = self.object.category
        ctx["filtered_articles"] = (
            PsychoArticle.objects
            .filter(is_active=True, category=self.object.category)
            .exclude(pk=self.object.pk)
            .order_by("-created_at")[:6]
        )
        return ctx


def article_filter(request):
    """HTMX：依分類篩選文章列表（文章詳頁底部用）。"""
    category = request.GET.get("category", "")
    exclude_id = request.GET.get("exclude", "")

    qs = PsychoArticle.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    articles = qs.order_by("-created_at")[:6]

    return render(request, "_partials/_article_grid.html", {
        "articles": articles,
        "filter_category": category,
    })


class ClinicsView(TemplateView):
    """診所指南（訪客可看，支援 HTMX 篩選）。"""
    template_name = "clinics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Clinic.objects.filter(is_active=True)

        county   = self.request.GET.get("county",   "").strip()
        ctype    = self.request.GET.get("type",     "").strip()
        district = self.request.GET.get("district", "").strip()

        if county and county != "全部":
            qs = qs.filter(county=county)
        if ctype and ctype != "全部":
            qs = qs.filter(clinic_type=ctype)
        if district and district != "全部":
            qs = qs.filter(district=district)

        # 一次撈出所有縣市 → 行政區對應表，給 Alpine 動態渲染用
        rows = (
            Clinic.objects.filter(is_active=True)
            .exclude(district="")
            .values("county", "district")
            .distinct()
            .order_by("county", "district")
        )
        all_districts: dict = {}
        for row in rows:
            all_districts.setdefault(row["county"], []).append(row["district"])

        ctx["clinics"]           = qs
        ctx["counties"]          = COUNTIES
        ctx["selected_county"]   = county or "全部"
        ctx["selected_type"]     = ctype or "全部"
        ctx["selected_district"] = district or "全部"
        ctx["type_choices"]      = [("全部", "全部"), ("諮商所", "諮商所"), ("身心科", "身心科")]
        ctx["districts_data"]    = all_districts
        return ctx

    def get_template_names(self):
        """HTMX 請求只回清單 partial，免整頁刷新。"""
        if self.request.headers.get("HX-Request"):
            return ["_partials/_clinic_list.html"]
        return [self.template_name]
