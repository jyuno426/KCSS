from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db.models import Min, Max, Q, Count, F
from django.db.models.functions import Concat
from .models import Conference, Publication, Author, Coauthorship
from .apps import KcssConfig


def build_context_data_for_index_view(context, is_women=False, is_sort=False):
    context["kcss_author"] = KcssConfig.author
    context["kcss_title"] = KcssConfig.title
    context["years"] = range(1960, timezone.now().year + 1)
    context["is_women"] = is_women
    context["is_sort"] = is_sort

    # ------ Construct field_table ------

    field_category_dict = {}
    for conference in Conference.objects.all().order_by("conf_name"):
        conf_name = conference.conf_name + ("*" if conference.on_csrankings else "")
        year_label = "({}-{})".format(
            *Publication.objects.filter(conf=conference)
            .aggregate(Min("year"), Max("year"))
            .values()
        )

        field_category = str(conference.field_category)
        conf_label = (conf_name, year_label)

        if field_category in field_category_dict:
            field_category_dict[field_category].append(conf_label)
        else:
            field_category_dict[field_category] = [conf_label]

    context["field_table"] = []
    for i, fc in enumerate(
        sorted(
            # sorting order:
            # 1. num of conferences in each field
            # 2. field category name
            field_category_dict.items(),
            key=lambda fc: (-len(fc[1]), fc[0],),
        )
    ):
        if i % 3 == 0:
            # Add one more row in field_table
            context["field_table"].append([])
        context["field_table"][-1].append(fc)

    # -----------------------------------


class IndexView(generic.TemplateView):
    template_name = "kcss/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        build_context_data_for_index_view(context)
        return context


class SortView(generic.TemplateView):
    template_name = "kcss/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        build_context_data_for_index_view(context, is_sort=True)
        return context


class WomenView(generic.TemplateView):
    template_name = "kcss/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        build_context_data_for_index_view(context, is_women=True)
        return context


class ResultsView(generic.TemplateView):
    template_name = "kcss/results.html"

    def get_context_data(self, **kwargs):
        query_dict = self.request.GET

        # Parse query parameters
        conf_list = query_dict.getlist("conferences")
        from_year = int(query_dict.get("from_year"))
        to_year = int(query_dict.get("to_year"))
        author_filter = query_dict.get("author_filter")
        author_limit = int(query_dict.get("author_limit"))
        min_num_pages = int(query_dict.get("min_num_pages"))
        canvas_height = KcssConfig.canvas_height[author_limit]

        try:
            is_sort = kwargs["type"] == "sort"
            is_women = kwargs["type"] == "women"
        except KeyError:
            is_sort = False
            is_women = False

        # Filter coauthorships based on query parameters
        coauthorships = (
            Coauthorship.objects.prefetch_related(
                "author", "publication", "publication__conf"
            )
            .filter(
                publication__conf__conf_name__in=conf_list,
                publication__year__gte=from_year,
                publication__year__lte=to_year,
            )
            .filter(
                Q(publication__num_pages=0)
                | Q(publication__num_pages__gte=min_num_pages)
            )
            # .annotate(num_authors=Count("publication__authors"))
        )

        if "korean" in author_filter:
            coauthorships = coauthorships.filter(author__korean_prob__gte=50)

        women_filter = query_dict.get("women_filter")
        if women_filter:
            coauthorships = coauthorships.filter(
                author__woman_prob__gte=int(women_filter)
            )

        if "first" in author_filter:
            coauthorships = coauthorships.filter(author_order=1)
        elif "last" in author_filter:
            coauthorships = coauthorships.annotate(
                num_authors=Count("publication__authors")
            ).filter(author_order=F("num_authors"))

        # Aggregate group-by authors and sort by num_publications
        authors_only = (
            coauthorships.values("author", "author__first_name", "author__last_name")
            .annotate(num_publications=Count("id"))
            .order_by("-num_publications", "author__first_name", "author__last_name")
        )

        # If no results, return.
        if not authors_only.exists():
            return {
                "result": [],
                "weight_dict": {},
                "canvas_height": canvas_height,
                "max_num_publications": 1,
                "is_women": is_women,
            }

        # Maximum of num_publications (to define edge weight and node size)
        max_num_publications = authors_only[0]["num_publications"]

        # Slice authors upto author_limit
        if authors_only.count() > author_limit:
            authors_only = authors_only.filter(
                num_publications__gte=authors_only[author_limit - 1]["num_publications"]
            )

        # Clean up results by author
        result_by_author = {}
        weight_dict = {}

        # Get author_id_list (to filter coauthorships)
        author_id_list = []

        for elem in authors_only.iterator():
            first_name = elem["author__first_name"]
            last_name = elem["author__last_name"]
            author_name = "{} {}".format(first_name, last_name)

            result_by_author[author_name] = {
                "publications": [],
                "num_publications_by_conf": {},
            }

            weight_dict[author_name] = {}

            author_id_list.append(elem["author"])

        # Finalize coauthorships table with authors
        coauthorships = coauthorships.filter(author__id__in=author_id_list)

        for elem in coauthorships.iterator():
            author_name = str(elem.author)
            conf_name = str(elem.publication.conf)
            coauthor_name_list = []
            for coauthor in elem.publication.authors.all().order_by("coauthorship"):
                coauthor_name_list.append(str(coauthor))

            # Update probability
            result_by_author[author_name]["probability"] = int(
                elem.author.woman_prob if women_filter else elem.author.korean_prob
            )

            # Update publications
            result_by_author[author_name]["publications"].append(
                {
                    "conf": conf_name,
                    "year": elem.publication.year,
                    "title": elem.publication.title,
                    "authors": ", ".join(coauthor_name_list),
                    "url": elem.publication.url,
                    # "num_pages": elem.publication.num_pages,
                }
            )

            # Update num_publications_by_conf
            by_conf = result_by_author[author_name]["num_publications_by_conf"]
            if conf_name in by_conf:
                by_conf[conf_name] += 1
            else:
                by_conf[conf_name] = 1

            # Update coauthor_weight
            for coauthor in coauthor_name_list:
                if coauthor not in result_by_author:
                    continue

                if coauthor in weight_dict[author_name]:
                    weight_dict[author_name][coauthor] += 1 / max_num_publications
                else:
                    weight_dict[author_name][coauthor] = 1 / max_num_publications

        # Final result
        result = []

        if is_sort:
            # sort by # of publications
            author_name_list = sorted(
                result_by_author.keys(),
                key=lambda author: -len(result_by_author[author]["publications"]),
            )
        else:
            author_name_list = sorted(result_by_author.keys())

        for author_name in author_name_list:
            probability = result_by_author[author_name]["probability"]
            publications = result_by_author[author_name]["publications"]
            publications.sort(key=lambda x: (x["conf"], -x["year"], x["title"]))

            by_conf = result_by_author[author_name]["num_publications_by_conf"]
            by_conf = ["{}={}".format(k.upper(), v) for k, v in sorted(by_conf.items())]
            num_publications_by_conf = ", ".join(by_conf)

            result.append(
                (author_name, probability, publications, num_publications_by_conf)
            )

        return {
            "result": result,
            "weight_dict": weight_dict,
            "canvas_height": canvas_height,
            "max_num_publications": max_num_publications,
            "is_women": is_women,
        }

