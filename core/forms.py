from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Servicio, Categoria, Factura, DetalleFactura


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['titulo', 'descripcion', 'precio', 'categoria']

    def clean_precio(self):
        precio = self.cleaned_data['precio']
        if precio <= 0:
            raise ValidationError('El precio debe ser mayor a 0.')
        return precio


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 2})}


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'fecha']
        widgets = {
            'fecha': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }


class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleFactura
        fields = ['servicio', 'cantidad']

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicio'].queryset = (
            Servicio.objects
            .filter(propietario=usuario)
            .select_related('categoria')
        )
        self.fields['servicio'].label_from_instance = (
            lambda s: f'{s.titulo} — ${s.precio}'
        )


DetalleFormSet = inlineformset_factory(
    Factura,
    DetalleFactura,
    form=DetalleFacturaForm,
    extra=3,
    min_num=1,
    validate_min=True,
    can_delete=False,
)