require 'json'

module Jekyll
  class Indexer < Generator
    def generate(site)
      index = []

      site.posts.docs.each do |post|
        index << {
          "title" => post.data['title'],
          "url" => post.url,
          "content" => post.content.gsub(/<\/?[^>]*>/, ""),
          "tags" => post.data['tags'],
          "paper" => post.data['paper'],
          "paper_url" => post.data['paper_url'],
        }
      end

      File.open("search.json", "w") do |file|
        file.write(JSON.pretty_generate(index))
      end
    end
  end
end
