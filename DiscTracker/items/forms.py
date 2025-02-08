from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class AddItemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-addItemForm"
        self.helper.form_class = "mainForms"
        self.helper.form_method = "post"
        self.helper.form_action = "add-item"

        self.helper.add_input(Submit("submit", "Add Item"))
    
    cex_id = forms.CharField(
        label="CEX ID", 
        max_length=100
    )

class UpdateItemPrices(forms.Form):
    # submit button
    pass