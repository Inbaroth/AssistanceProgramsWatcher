from django.db import models


# Create your models here.
class BaseData(models.Model):
    # assumption: name is one-to-one
    name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        abstract = True


# https://dev.to/sankalpjonna/using-abstract-models-in-django-1igi
class EligibleTreatment(BaseData):
    pass

    class Meta:
        verbose_name = 'EligibleTreatment'
        verbose_name_plural = 'EligibleTreatments'

    def __str__(self):
        return self.name


class AssistanceProgram(BaseData):
    status = models.BooleanField(default=0)
    grant_amount = models.IntegerField()
    url = models.CharField(max_length=255)
    currency = models.CharField(max_length=1, default="$")

    # creates and handle a relationship table
    treatments = models.ManyToManyField('EligibleTreatment', related_name='programs')    # https://www.revsys.com/tidbits/tips-using-djangos-manytomanyfield/ , https://www.sankalpjonna.com/learn-django/the-right-way-to-use-a-manytomanyfield-in-django

    class Meta:
        verbose_name = 'AssistanceProgram'
        verbose_name_plural = 'AssistancePrograms'

    def __str__(self):
        return self.name





