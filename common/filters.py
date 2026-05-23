import django_filters


class BaseFilter(django_filters.FilterSet):
    def filter_csv(self, queryset, field_name, value):
        values = [v.strip() for v in value.split(",") if v.strip()]
        return (
            queryset.filter(**{f"{field_name}__in": values}).distinct()
            if values
            else queryset
        )

    def filter_text(self, queryset, field_name, value):
        return queryset.filter(**{f"{field_name}__icontains": value}).distinct()
