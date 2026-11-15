module TableScroll
  TAG = %r{<(/?)table\b[^>]*>}i.freeze

  def self.wrap(html)
    out = +""
    depth = 0
    last = 0
    html.scan(TAG) do
      m = Regexp.last_match
      out << html[last...m.begin(0)]
      if m[1].empty?
        out << %(<div class="table-scroll">) if depth.zero?
        depth += 1
        out << m[0]
      else
        out << m[0]
        depth -= 1 if depth.positive?
        out << "</div>" if depth.zero?
      end
      last = m.end(0)
    end
    out << html[last..]
  end
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  doc.output = TableScroll.wrap(doc.output) if doc.output_ext == ".html" && doc.output.include?("<table")
end
