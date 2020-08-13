# Generated by Django 3.0.8 on 2020-07-29 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conf_name', models.CharField(max_length=20, unique=True)),
                ('full_name', models.CharField(max_length=200, unique=True)),
                ('published_years', models.TextField(max_length=200)),
            ],
            options={
                'ordering': ['conf_name'],
            },
        ),
        migrations.CreateModel(
            name='FieldCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=200, unique=True)),
                ('on_csrankings', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['field_name'],
            },
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=200, unique=True)),
                ('url', models.URLField()),
                ('num_pages', models.IntegerField(default=0)),
                ('conf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kcss.Conference')),
            ],
            options={
                'ordering': ['conf', 'year', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=50)),
                ('korean_prob', models.FloatField(default=0)),
                ('woman_prob', models.FloatField(default=0)),
                ('publications', models.ManyToManyField(to='kcss.Paper')),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
    ]
