from django import forms
from .models import UserProfile


# ============================================================
# CONSTANTS — must be defined BEFORE any class that uses them
# ============================================================
ALLOWED_IMAGE_EXT = ["jpg", "jpeg", "png", "webp", "gif"]
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB


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


# ============================================================
# CONTACT
# ============================================================
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


# ============================================================
# CHECKOUT
# ============================================================
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


# ============================================================
# PROFILE / AVATAR UPLOAD
# ============================================================
class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["avatar", "bio", "phone"]
        widgets = {
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
            "bio": forms.TextInput(attrs={
                "placeholder": "One line about you (optional)",
                "maxlength": 200,
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "07XX XXX XXX",
            }),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        # Only validate if it's a new upload (not an existing file)
        if hasattr(avatar, "size"):
            if avatar.size > MAX_AVATAR_SIZE:
                raise forms.ValidationError("Image must be under 2 MB.")

            ext = avatar.name.rsplit(".", 1)[-1].lower() if "." in avatar.name else ""
            if ext not in ALLOWED_IMAGE_EXT:
                raise forms.ValidationError(
                    f"Only {', '.join(e.upper() for e in ALLOWED_IMAGE_EXT)} files are allowed."
                )

        return avatar