module SocialCard
  DEFAULT = "/assets/img/social-card.png".freeze

  class Generator < Jekyll::Generator
    def generate(site)
      site.posts.docs.each do |post|
        next unless post.data["image"] == DEFAULT

        card = "/assets/img/social/#{post.basename_without_ext.sub(/\A\d{4}-\d{2}-\d{2}-/, "")}.png"
        post.data["image"] = card if File.exist?(site.in_source_dir(card))
      end
    end
  end
end
