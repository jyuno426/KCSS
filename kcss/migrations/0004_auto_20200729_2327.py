# Generated by Django 3.0.8 on 2020-07-29 14:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kcss', '0003_auto_20200729_2313'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='field_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='kcss.FieldCategory'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='conf',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='kcss.Conference'),
        ),
    ]
