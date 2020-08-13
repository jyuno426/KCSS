import json
from django.core.management.base import BaseCommand, CommandError
from kcss.models import Author, Publication, Conference, Coauthorship


class Command(BaseCommand):
    help = "Update new publications from crawled json file(e.g. icml2020.json)"

    def add_arguments(self, parser):
        parser.add_argument("conf_name", type=str, help="conference name")
        parser.add_argument("year", type=int, help="published year")

    def handle(self, *args, **options):
        conf_name = options["conf_name"]
        year = options["year"]

        filepath = "kcss/static/json/publications/{}/{}{}.json".format(
            conf_name.upper(), conf_name.lower(), year,
        )
        publications = json.load(open(filepath))
        conf = Conference.objects.get(conf_name=conf_name)

        for _publication in publications:
            title, authors, url, num_pages = _publication

            publication = Publication(
                conf=conf, year=year, title=title, url=url, num_pages=num_pages
            )
            publication.save()

            for i, author_name in enumerate(authors):
                name_parts = author_name.split()
                last_name = name_parts[-1]
                first_name = " ".join(name_parts[:-1])
                # try:
                author = Author.objects.get(first_name=first_name, last_name=last_name)
                # except Author.DoesNotExist:
                #     author = Author(
                #         first_name=first_name,
                #         last_name=last_name,
                #         korean_prob=korean_prob,
                #         woman_prob=woman_prob,
                #     )
                #     author.save()

                coauthorship = Coauthorship(
                    publication=publication, author=author, number=i + 1
                )
                coauthorship.save()

            self.stdout.write(self.style.SUCCESS(title))

