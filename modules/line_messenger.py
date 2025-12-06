from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, SeparatorComponent, ButtonComponent, URIAction, IconComponent

class LineMessenger:
    @staticmethod
    def create_analysis_flex_message(analysis_result, restaurant_name, map_url):
        """
        Creates a Line Flex Message based on the AI analysis result.
        """
        
        # Determine header color based on risk level
        risk_level = analysis_result.get('risk_level', 'Low')
        header_color = "#1DB446" # Green (Safe)
        if risk_level == 'High':
            header_color = "#D93025" # Red
        elif risk_level == 'Medium':
            header_color = "#F4B400" # Yellow

        # Recommended dishes text
        dishes = analysis_result.get('recommended_dishes', [])
        dishes_text = "、".join(dishes) if dishes else "無特別推薦"

        # Construct the Bubble
        bubble = BubbleContainer(
            header=BoxComponent(
                layout='vertical',
                background_color=header_color,
                contents=[
                    TextComponent(text="食探 AI 分析報告", weight='bold', color='#FFFFFF', size='sm'),
                    TextComponent(text=restaurant_name, weight='bold', color='#FFFFFF', size='xl', margin='md', wrap=True)
                ]
            ),
            hero=None, # Can add an image here if we scraped one
            body=BoxComponent(
                layout='vertical',
                contents=[
                    # Warning / Status
                    BoxComponent(
                        layout='vertical',
                        margin='md',
                        contents=[
                            TextComponent(text=analysis_result.get('warning_message', '分析完成'), wrap=True, size='sm', color='#666666')
                        ]
                    ),
                    SeparatorComponent(margin='md'),
                    
                    # Real Score
                    BoxComponent(
                        layout='baseline',
                        margin='md',
                        contents=[
                            TextComponent(text="真實評分", color='#aaaaaa', size='sm', flex=2),
                            TextComponent(text=f"{analysis_result.get('real_score', 'N/A')} ⭐️", weight='bold', color='#333333', size='xl', flex=4)
                        ]
                    ),
                    TextComponent(text=analysis_result.get('reason', ''), size='xs', color='#aaaaaa', wrap=True, margin='sm'),
                    
                    SeparatorComponent(margin='md'),
                    
                    # Recommended Dishes
                    BoxComponent(
                        layout='vertical',
                        margin='md',
                        contents=[
                            TextComponent(text="必吃推薦", color='#aaaaaa', size='sm'),
                            TextComponent(text=dishes_text, weight='bold', color='#333333', size='md', wrap=True, margin='sm')
                        ]
                    ),
                    
                    SeparatorComponent(margin='md'),
                    
                    # Summary
                    BoxComponent(
                        layout='vertical',
                        margin='md',
                        contents=[
                            TextComponent(text="一句話總結", color='#aaaaaa', size='sm'),
                            TextComponent(text=analysis_result.get('summary', ''), size='sm', color='#333333', wrap=True, margin='sm')
                        ]
                    )
                ]
            ),
            footer=BoxComponent(
                layout='vertical',
                contents=[
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='開啟 Google Maps', uri=map_url)
                    )
                ]
            )
        )

        return FlexSendMessage(alt_text=f"{restaurant_name} 的 AI 分析報告", contents=bubble)

    @staticmethod
    def create_error_message(error_text):
        return FlexSendMessage(
            alt_text="發生錯誤",
            contents=BubbleContainer(
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(text="⚠️ 錯誤", weight='bold', color='#D93025'),
                        TextComponent(text=error_text, wrap=True, margin='md')
                    ]
                )
            )
        )
