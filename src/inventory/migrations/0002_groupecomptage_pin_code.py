from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupecomptage",
            name="pin_code",
            field=models.CharField(
                default="0000",
                help_text="Code PIN requis pour valider la selection du groupe.",
                max_length=12,
                verbose_name="Code PIN",
            ),
        ),
    ]
