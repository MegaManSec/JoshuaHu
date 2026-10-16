module MarkdownSource
  class Copy < Jekyll::StaticFile
    attr_reader :url

    def initialize(site, item)
      super(site, site.source, File.dirname(item.relative_path), File.basename(item.relative_path))
      @url = "#{item.url}.md"
    end
  end

  class Generator < Jekyll::Generator
    def generate(site)
      menu_pages = site.pages.select { |page| page.relative_path.start_with?("menu/") }
      (site.posts.docs + menu_pages).each do |item|
        copy = Copy.new(site, item)
        item.data["markdown_url"] = copy.url
        site.static_files << copy
      end
    end
  end
end
