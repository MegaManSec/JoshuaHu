require "kramdown"

module LongInlineCode
  PHRASE_MIN = 20
  PHONE_LINE_CHARS = 38

  def convert_codespan(el, indent)
    html = super
    text = el.value
    phrase = text.length >= PHRASE_MIN && text.strip.match?(/\s/)
    return html unless phrase || text.length >= PHONE_LINE_CHARS

    match = html.match(%r{\A<code(?<attrs>[^>]*)>[^<]*</code>\z})
    return html unless match

    attrs = match[:attrs]
    attrs = attrs.include?('class="') ? attrs.sub(/class="([^"]*)"/) { %(class="#{Regexp.last_match(1)} long") } : %(#{attrs} class="long")
    body = text.split(/(\s+)/).map do |part|
      if part.empty? || part.match?(/\A\s+\z/) || part.length >= PHONE_LINE_CHARS
        escape_html(part)
      else
        "<span>#{escape_html(part)}</span>"
      end
    end.join
    "<code#{attrs}>#{body}</code>"
  end
end

Kramdown::Converter::Html.prepend(LongInlineCode)
