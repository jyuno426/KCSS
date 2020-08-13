import datetime
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


def current_year():
    """
    Get current year of the timezone
    """
    return timezone.now().year


def min_year_validator(year):
    """
    Validates the year >= 1960
    """
    return MinValueValidator(1960)(year)


def max_year_validator(year):
    """
    Validates the year <= current_year()
    """
    return MaxValueValidator(current_year())(year)


class FieldCategory(models.Model):
    field_name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["field_name"]

    def __str__(self):
        return self.field_name


class Conference(models.Model):
    field_category = models.ForeignKey(
        FieldCategory, on_delete=models.SET_NULL, null=True
    )
    conf_name = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    on_csrankings = models.BooleanField(default=False)

    # This may be needed to avoid unnecessary queries
    # published_years = models.TextField(max_length=200)

    class Meta:
        ordering = ["field_category", "conf_name"]

    def __str__(self):
        return self.conf_name


class Author(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=50)
    korean_prob = models.FloatField(default=0)
    woman_prob = models.FloatField(default=0)

    class Meta:
        ordering = ["last_name", "first_name"]
        unique_together = ("first_name", "last_name")

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


class Publication(models.Model):
    conf = models.ForeignKey(Conference, on_delete=models.SET_NULL, null=True)
    year = models.IntegerField(validators=[min_year_validator, max_year_validator])
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(
        Author,
        through="Coauthorship",
        through_fields=["publication", "author"],
        db_index=True,
        related_name="publications",
    )
    url = models.URLField(max_length=200)
    num_pages = models.IntegerField(default=0)

    class Meta:
        ordering = ["conf", "year", "title"]
        unique_together = ("conf", "year", "title")

    def __str__(self):
        return "[{}][{}][{}]".format(self.conf, self.year, self.title)


class Coauthorship(models.Model):
    publication = models.ForeignKey(
        Publication, on_delete=models.CASCADE, db_index=True
    )
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, db_index=True, related_name="coauthorship"
    )
    author_order = models.PositiveIntegerField()

    class Meta:
        ordering = ["publication", "author_order"]
        unique_together = (
            "publication",
            "author",
            "author_order",
        )

    def __str__(self):
        return "{} of {}".format(self.author, self.publication)
