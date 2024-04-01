from htmlToMarkdown import md_crawl
url = 'https://docs.truefoundry.com'
print(f'🕸️ Starting crawl of {url}')
md_crawl(
    url,
    max_depth=3,
    num_threads=8,
    base_dir='tf-docs',
    valid_paths=['/docs'],
    target_content=['div#content', 'article', 'div', 'main', 'p', 'h1', 'h2', 'h3', 'h4'],
    is_domain_match=True,
    is_base_path_match=False,
    is_debug=True
)