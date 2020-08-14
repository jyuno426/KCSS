import json
from django.core.management.base import BaseCommand, CommandError
from kcss.models import Author


class Command(BaseCommand):
    help = "Update koreans that are hard coded"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        bp = "kcss/static/kcss/"

        with open(bp + "data/author_name_dict.json") as f:
            author_name_dict = json.load(f)

        with open(bp + "data/kr_hard_coding.txt") as f:
            for line in f.readlines():
                author_name = line.strip()

                if author_name in author_name_dict:
                    author_name = author_name_dict[author_name]

                name_parts = author_name.split()
                last_name = name_parts[-1]
                first_name = " ".join(name_parts[:-1])

                try:
                    author = Author.objects.get(
                        first_name=first_name, last_name=last_name
                    )
                except Author.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            "{} {} does not exist in DB".format(first_name, last_name)
                        )
                    )

                author.korean_prob = 100
                author.save()
                self.stdout.write(self.style.SUCCESS(str(author)))

