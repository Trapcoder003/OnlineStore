from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


KENYA_COUNTIES = [
    ("Nairobi", "Nairobi"),
    ("Mombasa", "Mombasa"),
    ("Kisumu", "Kisumu"),
    ("Nakuru", "Nakuru"),
    ("Eldoret", "Eldoret"),
    ("Thika", "Thika"),
    ("Kiambu", "Kiambu"),
    ("Machakos", "Machakos"),
    ("Kakamega", "Kakamega"),
    ("Meru", "Meru"),
    ("Kisii", "Kisii"),
    ("Nyeri", "Nyeri"),
    ("Other", "Other"),
]

DELIVERY_CHOICES = [
    ("pickup",   "Pickup at store (Free)"),
    ("standard", "Standard delivery — KES 300"),
    ("express",  "Express delivery — KES 500"),
]


class CheckoutForm(forms.Form):
    # Contact
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "07XX XXX XXX"}),
    )

    # Shipping
    ship_name = forms.CharField(max_length=120, label="Full name")
    ship_phone = forms.CharField(
        max_length=20,
        label="Recipient phone",
        widget=forms.TextInput(attrs={"placeholder": "07XX XXX XXX"}),
    )
    ship_county = forms.ChoiceField(choices=KENYA_COUNTIES, label="County")
    ship_town = forms.CharField(
        max_length=80,
        label="Town / area",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Kilimani"}),
    )
    ship_address = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Building, street, landmark",
        }),
        label="Address details",
    )
    delivery_method = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        initial="standard",
        widget=forms.RadioSelect,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Optional instructions (delivery notes, gate code, etc.)",
        }),
    )