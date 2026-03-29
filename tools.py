from duckduckgo_search import DDGS
import requests
import xml.etree.ElementTree as ET
from langchain_core.tools import tool

@tool
def search_internet(query: str) -> str:
    """
    SỬ DỤNG CÔNG CỤ NÀY KHI người dùng hỏi về: tin tức chung, sự kiện hiện tại, thời tiết, nhân vật, kiến thức tổng hợp, hoặc các thông tin không thuộc mảng tài chính.
    Đầu vào (query) là từ khóa tìm kiếm (ví dụ: "tin tức công nghệ hôm nay", "thời tiết Hà Nội").
    """
    print(f"🕵️‍♂️ Aley đang tìm kiếm trên mạng: {query}")
    try:
        results = []
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(query, max_results=3)
            for r in ddgs_gen:
                results.append(f"Tiêu đề: {r['title']}\nNội dung: {r['body']}\nLink: {r['href']}")

        if not results:
            return "Không tìm thấy thông tin nào trên mạng."

        return "\n\n--\n\n".join(results)

    except Exception as e:
        return f"Lỗi khi tìm kiếm: {e}"
	
@tool
def get_financial_data(query: str) -> str:
    """
    SỬ DỤNG CÔNG CỤ NÀY BẮT BUỘC KHI người dùng hỏi về: giá vàng, tỷ giá ngoại tệ, chứng khoán.
    Đầu vào (query) truyền vào loại tài sản người dùng muốn hỏi (ví dụ: "giá vàng", "usd", "cổ phiếu fpt").
    """
    query_lower = query.lower()
    
    if "vàng" in query_lower:
        try:
            url = "https://sjc.com.vn/xml/tygiavang.xml"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                tree = ET.fromstring(response.content)
                
                updated_time = tree.find('.//ratelist').attrib.get('updated', 'Không rõ')
                
                hcm_city = tree.find('.//city[@name="Hồ Chí Minh"]')
                if hcm_city is not None:
                    first_item = hcm_city.find('item') # Thường là loại SJC 1L - 10L
                    
                    buy_price = first_item.attrib.get('buy', '0')
                    sell_price = first_item.attrib.get('sell', '0')
                    gold_type = first_item.attrib.get('type', 'Vàng SJC')
                    
                    return (f"THÔNG TIN CHÍNH THỨC TỪ SJC (Cập nhật lúc {updated_time}): "
                            f"Loại {gold_type}. "
                            f"Giá mua vào: {buy_price} triệu VNĐ/lượng. "
                            f"Giá bán ra: {sell_price} triệu VNĐ/lượng.")
            
            return "Hiện tại hệ thống SJC đang bảo trì, không thể lấy giá vàng."
            
        except Exception as e:
            return f"Đã xảy ra lỗi kỹ thuật khi kết nối đến trạm dữ liệu vàng: {str(e)}"

    elif "chứng khoán" in query_lower or "cổ phiếu" in query_lower:
        return "Tính năng tra cứu chứng khoán đang được Giám đốc xây dựng. Hãy quay lại sau nhé!"
        
    elif "usd" in query_lower or "ngoại tệ" in query_lower:
        return "Tính năng tra cứu tỷ giá ngoại tệ đang được Giám đốc xây dựng. Hãy quay lại sau nhé!"
    else:
        return f"Hiện tại Aley chưa được trang bị công cụ để tra cứu loại dữ liệu: {query}"
