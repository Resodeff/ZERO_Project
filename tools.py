from duckduckgo_search import DDGS

def search_internet(query):
	print(f"Đang tìm kiếm trên web: {query}")
	try:
		results = []
		with DDGS() as ddgs:
			ddgs_gen = ddgs.text(query, max_results = 3)
			for r in ddgs_gen:
				results.append(f"Tiêu đề: {r['title']}\nNội dung: {r['body']}\nLink: {r['href']}")

		if not results:
			return "Không tìm thấy thông tin nào trên mạng"

		return "\n\n--\n\n".join(results)

	except Exception as e:
		return f"Lội khi tìm kiếm: {e}"