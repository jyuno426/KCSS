import os, json
from django.core.management.base import BaseCommand, CommandError
from kcss.models import Author, Publication, Conference, Coauthorship
from utils.lstm_model import LSTM_Model


class Command(BaseCommand):
    help = "Update all publications from crawled json files"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        bp = "kcss/static/kcss/"

        author_name_dict = json.load(open(bp + "json/author_name_dict.json"))
        korean_prob_dict = json.load(open(bp + "json/korean_prob_dict.json"))
        woman_prob_dict = json.load(open(bp + "json/woman_prob_dict.json"))

        korean_prob_model = LSTM_Model(bp + "lstm_models/korean_prob_model.h5")
        woman_prob_model = LSTM_Model(bp + "lstm_models/woman_prob_model.h5")

        conf_list = os.listdir(bp + "json/publications")
        for i, conf_name in enumerate(conf_list):

            year_list = os.listdir(bp + "json/publications/" + conf_name)
            for j, filename in enumerate(year_list):

                year = int(filename[len(conf_name) : -5])
                filepath = bp + "json/publications/{}/{}{}.json".format(
                    conf_name.upper(), conf_name.lower(), year,
                )
                publications = json.load(open(filepath))
                conf = Conference.objects.get(conf_name__iexact=conf_name)

                for k, _publication in enumerate(publications):
                    _title, _author_name_list, url, num_pages = _publication

                    title = _title.strip().strip(".")
                    author_name_list = [
                        author_name_dict[author_name]
                        if author_name in author_name_dict
                        else author_name
                        for author_name in _author_name_list
                    ]

                    try:
                        publication = Publication.objects.get(
                            conf=conf, year=year, title=title
                        )
                    except Publication.DoesNotExist:
                        publication = Publication(
                            conf=conf,
                            year=year,
                            title=title,
                            url=url,
                            num_pages=num_pages,
                        )
                        publication.save()

                    for author_order, author_name in enumerate(author_name_list):
                        name_parts = author_name.split()
                        last_name = name_parts[-1]
                        first_name = " ".join(name_parts[:-1])

                        try:
                            author = Author.objects.get(
                                first_name=first_name, last_name=last_name
                            )
                        except Author.DoesNotExist:
                            if first_name in korean_prob_dict:
                                korean_prob = korean_prob_dict[first_name]
                            else:
                                korean_prob = int(
                                    100 * korean_prob_model.pred(first_name)
                                )

                            if first_name in woman_prob_dict:
                                woman_prob = woman_prob_dict[first_name]
                            else:
                                woman_prob = 0

                            author = Author(
                                first_name=first_name,
                                last_name=last_name,
                                korean_prob=korean_prob,
                                woman_prob=woman_prob,
                            )
                            author.save()

                        if not Coauthorship.objects.filter(
                            publication=publication,
                            author=author,
                            number=author_order + 1,
                        ).exists():
                            Coauthorship(
                                publication=publication,
                                author=author,
                                number=author_order + 1,
                            ).save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            "(conf: {}/{}) (year: {}/{}) (publ: {}/{}) - {}".format(
                                i + 1,
                                len(conf_list),
                                j + 1,
                                len(year_list),
                                k + 1,
                                len(publications),
                                title,
                            )
                        )
                    )

