module DoubleHyphenFlags
  FLAG = /(?<![\w-])--(?=\w)/.freeze
  MARK = "\u{E000}".freeze

  def markdownify(input)
    super(input.to_s.gsub(FLAG, MARK * 2)).gsub(MARK, "-")
  end

  def smartify(input)
    super(input.to_s.gsub(FLAG, MARK * 2)).gsub(MARK, "-")
  end
end

Jekyll::Filters.prepend(DoubleHyphenFlags)
