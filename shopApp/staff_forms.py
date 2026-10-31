from django import forms
from django.utils.text import slugify

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "slug",
            "description",
            "price",
            "old_price",
            "stock",
            "image",
            "brand",
            "is_featured",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Wireless Earbuds"}),
            "slug": forms.TextInput(attrs={"placeholder": "auto-generated from name if blank"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Short description of the product..."}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "old_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
            "brand": forms.TextInput(attrs={"placeholder": "Optional"}),
        }
        help_texts = {
            "slug": "Leave blank to auto-generate from name.",
            "old_price": "Optional. Original price before discount.",
            "image": "Square image recommended. Max 2 MB.",
        }
        labels = {
            "is_featured": "Feature this product on the homepage",
        }

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        name = (self.cleaned_data.get("name") or "").strip()

        if not slug and name:
            slug = slugify(name)

        if not slug:
            raise forms.ValidationError("Slug is required.")

        qs = Product.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A product with this slug already exists. Choose another.")
        return slug

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None or price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price

    def clean_old_price(self):
        old_price = self.cleaned_data.get("old_price")
        price = self.cleaned_data.get("price")
        if old_price and price and old_price <= price:
            raise forms.ValidationError("Old price must be higher than current price.")
        return old_price