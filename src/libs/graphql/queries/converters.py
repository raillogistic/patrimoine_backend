##################################################################

def get_choices(field):
    """get choices from given fields"""
    choices = field.__dict__["choices"]
    if choices is None:
        return None
    res = []

    for c in choices:
        value, label = c
        res.append({
            "value":value.upper(), "label":label
        })
    return res

##################################################################



def convert_nested(field, _type, get_fields,exclude=[]):
    class_name = field.__class__.__name__

    name = field.name
    required = not field.null
    if class_name == "ManyToOneRel":
        title = field.related_name
        _type = 'array'
    else:
        title = getattr(field, 'verbose_name',
                        getattr(field, 'related_name', ''))
    return {
                "name":name, 
                "title":title, 
                "required":required, 
                "is_property":False,
                "_type":_type,
                "fields":filter(lambda x: x.name not in exclude and "_ptr" not in x.name, get_fields(field.related_model))
        }


def convert_field(field):
    class_name = field.__class__.__name__
    name = field.name
    required = not field.null
    title = getattr(field, "verbose_name", "")
    if class_name == "CharField":
        if field.__dict__['choices'] is not None:
            return {
                "_type":"options", 
                "title":title, 
                "choices":get_choices(field), 
                "name":name, 
                "required":required
            }
        else:
            return {
                "_type":convert_simple_type(class_name), 
                "title":title, 
                "name":name, 
                "required":required
            }

    if class_name == "IntegerField" or class_name == "BigIntegerField" or class_name == "FileField" or class_name == "TimeField" or class_name == "FloatField" or class_name == "BooleanField" or class_name == "DateField" or class_name == "DateTimeField" or class_name == "TextField":
        res = {
            "_type":convert_simple_type(class_name),
            "title":title, 
            "name":name, 
            "required":required
        }
        return res
    if class_name == "ForeignKey" or class_name == "OneToOneField":
        return {
            "_type":convert_simple_type(class_name),
            "title":title, 
            "name":name, 
            "required":required, 
            "query":f"{field.related_model.__name__.lower()}s"
        }

    return None

def convert_manytomany(field):
    class_name = field.__class__.__name__
    name = field.name
    required = not field.null
    title = getattr(field, "verbose_name", "")

    return {
        "_type":convert_simple_type(class_name),
        "many":True,
        "title":title, 
        "name":name, 
        "required":required, 
        "query":f"{field.related_model.__name__.lower()}s"
    }


def convert_simple_type(_type):
    switcher = {
        "CharField": "text",
        "TextField": "textarea",
        "FloatField": "number",
        "IntegerField": "number",
        "BigIntegerField": "number",
        "DateTimeField": "datetime",
        "DateField": "date",
        "TimeField": "time",
        "BooleanField": "boolean",
        "ForeignKey": "query",
        "OneToOneField": "query",
        "FileField": "file",
    }

    return switcher.get(_type, "none")
