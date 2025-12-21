from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_groupecomptage_pin_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupecomptage",
            name="lieux_autorises",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "Lieux sur lesquels le groupe est autorise a operer. "
                    "Les sous-lieux des parents selectionnes sont aussi autorises."
                ),
                related_name="groupes_autorises",
                to="immo.location",
                verbose_name="Lieux autorises",
            ),
        ),
    ]
