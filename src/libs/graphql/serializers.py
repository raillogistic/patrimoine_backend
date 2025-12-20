from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from rest_framework import serializers


class CustomSerializer(serializers.ModelSerializer):
    def validate(self, data):
        m2m_fields = [
            field.name
            for field in self.Meta.model._meta.get_fields()
            if field.many_to_many
        ]

        # Remove Many-to-Many fields from data
        m2m_data = {
            field: data.pop(field, None)
            for field in [*m2m_fields, *getattr(self.Meta.model, "manytomanys", [])]
            if field in data
        }

        # Create an instance without the Many-to-Many fields for validation
        instance = self.Meta.model(**data)

        # Call the model's clean() method
        try:
            try:
                instance.clean(manytomany=m2m_data)
            except DjangoValidationError as e:
                # Convert Django's ValidationError to DRF's ValidationError
                raise DjangoValidationError(e.message_dict)
        except TypeError:
            pass
        # Add the Many-to-Many field data back to the validated data
        data.update(m2m_data)

        # Return the data if no validation errors are found
        return data


""""
example of using clean validation in a model

from django.core.exceptions import ValidationError
def clean(self):
		if  self.numero_fin<self.numero_debut:
			raise ValidationError({'numero_fin': 'Age cannot be negative.'})
"""


""" 
        # on serializers.ModelSerializer=>  def create 
        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                
                try:
                    field.set([v.id for v in value])
                    
                except Exception as E:
                    field.set(value)
                    print("errorxxxxxxxx",E)
"""
