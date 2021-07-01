# Create your views here.
from django.shortcuts import render
from rest_framework import generics
from .models import AssistanceProgram, EligibleTreatment
from .serializers import AssistanceProgramSerializer, EligibleTreatmentSerializer


class ListProgramView(generics.ListAPIView):
    queryset = AssistanceProgram.objects.all()  # used for returning objects from this view
    serializer_class = AssistanceProgramSerializer


class ListEligibleTreatmentView(generics.ListAPIView):
    queryset = EligibleTreatment.objects.all()  # used for returning objects from this view
    serializer_class = EligibleTreatmentSerializer
