from django.contrib import admin
from .models import WatchTask, ScrapedItem

# 让后台显示更详细的列，而不仅仅是一个名字
@admin.register(WatchTask)
class WatchTaskAdmin(admin.ModelAdmin):
    list_display = ('keywords', 'max_price', 'platform', 'is_active', 'created_at')
    list_filter = ('is_active', 'platform')

@admin.register(ScrapedItem)
class ScrapedItemAdmin(admin.ModelAdmin):
    # 在列表页显示标题、价格、发现时间，并点击标题可跳转
    list_display = ('title', 'price', 'found_at', 'url_link')
    search_fields = ('title',) # 支持搜索标题
    list_filter = ('found_at', 'task') # 右侧侧边栏筛选

    # 自定义一个方法，让 URL 变成可以点击的链接
    def url_link(self, obj):
        from django.utils.html import format_html
        return format_html("<a href='{0}' target='_blank'>查看商品</a>", obj.url)
    url_link.short_description = '商品链接'

# Register your models here.
