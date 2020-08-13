from django.contrib import admin
from django.db.models import Count
from .models import FieldCategory, Conference, Publication, Author, Coauthorship


class ConferenceInline(admin.TabularInline):
    model = Conference
    extra = 0


@admin.register(FieldCategory)
class FieldCategoryAdmin(admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("field_name",),}),)
    inlines = [ConferenceInline]
    list_display = ["field_name"]


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {"fields": ("field_category", "conf_name", "full_name", "on_csrankings"),},
        ),
    )
    list_display = ["conf_name", "field_category", "on_csrankings"]


class CoauthorshipInline(admin.TabularInline):
    model = Coauthorship
    extra = 0
    readonly_fields = ("publication", "author")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("publication", "author")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "korean_prob",
                    "woman_prob",
                    # "publications",
                ),
            },
        ),
    )
    search_fields = ("first_name", "last_name")
    inlines = (CoauthorshipInline,)
    list_display = [
        "first_name",
        "last_name",
        "korean_prob",
        "woman_prob",
        "num_publications",
    ]
    # filter_horizontal = ("Publication",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_num_publications=Count("publications"))
        return qs

    def publications(self, obj):
        return "haha"

    def num_publications(self, obj):
        return obj._num_publications

    num_publications.admin_order_field = "_num_publications"


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("conf", "year", "title", "url", "num_pages"),}),)
    search_fields = ("title",)
    inlines = (CoauthorshipInline,)
    list_display = ["title", "conf", "year"]
    list_filter = ("num_pages", "conf", "year")
