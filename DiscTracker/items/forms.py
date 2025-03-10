from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Field


class AddItemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-addItemForm"
        self.helper.form_class = "mainForms"
        self.helper.form_method = "post"
        self.helper.form_action = "add-item"
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Field("cex_id", placeholder="Enter CEX ID..."),
            Submit("submit", "Add Item"),
        )

    cex_id = forms.CharField(label="CEX ID", max_length=100)


class UpdateItemPrices(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-updateItemPricesForm"
        self.helper.form_class = "mainForms"
        self.helper.form_method = "post"
        self.helper.form_action = "update-item-prices"
        self.helper.layout = Layout(
            Submit("submit", "Update Item Prices", css_class="btn btn-secondary"),
        )


class DeleteItemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-deleteItemForm"
        self.helper.form_class = "mainForms"
        self.helper.form_method = "post"
        self.helper.form_action = "delete"
        self.helper.layout = Layout(
            Submit(
                "submit", "Delete From Collection", css_class="btn btn-danger bt btn-sm"
            ),
        )
