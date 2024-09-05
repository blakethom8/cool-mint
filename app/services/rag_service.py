knowledge_base = {
    "products": [
        {
            "title": "TechGear SmartHome Hub Compatibility",
            "content": "The TechGear SmartHome Hub is compatible with a wide range of smart home devices, including Philips Hue lights, Nest thermostats, and Amazon Echo devices. It uses standard protocols like Zigbee, Z-Wave, and Wi-Fi to connect and control various smart home products.",
        },
    ],
    "policies": [
        {
            "title": "Remote Work Policy",
            "content": "TechGear allows employees to work remotely for up to two weeks per quarter, including from different states. Employees must inform their manager and HR at least one week in advance. Ensure you have a stable internet connection and can attend all necessary meetings. For longer remote work periods or international travel, special approval is required from HR and your department head.",
        },
    ],
}


class RAGService:
    def __init__(self):
        # Initialize your actual RAG service here
        self.knowledge_base = knowledge_base

    def search(self, query: str = None) -> dict:
        return self.knowledge_base
