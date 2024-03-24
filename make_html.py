import json
import os

recommendation_scores = {
    'Clear Reject': 2,
    'Weak Reject': 3,
    'Borderline Reject': 4,
    'Borderline Accept': 5,
    'Weak Accept': 6,
    'Clear Accept': 7,
    'Strong Accept': 8,
}

def get_score(review):
    try:
        return recommendation_scores[review['Questions'][6]['Answers'][0]['Text'].split('.')[0]]
    except:
        return None


def build_html(conference):
    # Start creating the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Review Analysis</title>
        <style>
            body { font-family: apple-system, Arial, sans-serif; max-width: 1000px; margin: 0 auto; }
            details { margin-top: 10px; border: 1px solid #aaa; border-radius: 4px; padding: 10px 5px; }
            summary { font-weight: bold; cursor: pointer; padding: 5px 0; }
            ul { margin-top: 5px; padding-left: 15px; }
            li { margin-bottom: 5px; }
            .discussion { background-color: #f0f0f0; padding: 10px; margin-top: 10px; }
            .message { margin-top: 10px; }
            .author { font-weight: bold; }
            .date { font-size: 0.8em; color: #666; }
        </style>
    </head>
    <body>
        <h2>Paper Reviews</h2>
    """

    paper_ids = json.load(open(f'data/{conference}/paper_ids.json'))

    have_added_awaiting_decision_separator = False

    for paper in sorted(paper_ids, key=lambda x: (int(x["Status"] != "Awaiting Decision"), int(x["Id"]))):
        subfolder_path = os.path.join(f'data/{conference}', str(paper["Id"]))
        if os.path.isdir(subfolder_path):

            if paper["Status"] != "Awaiting Decision" and not have_added_awaiting_decision_separator:
                html_content += "<h2>Already Decided</h2>"
                have_added_awaiting_decision_separator = True

            reviews_file_path = os.path.join(subfolder_path, 'Reviews.json')
            discussion_file_path = os.path.join(subfolder_path, 'DiscussionMessages.json')

            if os.path.isfile(reviews_file_path):
                # Load the reviews data from the file
                with open(reviews_file_path) as f:
                    reviews_data = json.load(f)['value']

                if os.path.isfile(discussion_file_path):
                    # Load the discussion data from the file
                    with open(discussion_file_path) as f:
                        discussion_data = json.load(f)['value']
                else:
                    discussion_data = []

                number_real_messages = len([message for message in discussion_data if "The discussion is open now" not in message['Text']])

                # Paper summary
                paper_title = reviews_data[0]['SubmissionTitle']
                paper_number = f"<span style='font-weight: normal'>{reviews_data[0]['SubmissionId']}</span>"
                num_reviews = len(reviews_data)
                review_scores = [get_score(review) for review in reviews_data]
                review_scores = " / ".join([str(score) for score in review_scores])
                paper_summary = f"{paper_number} \"{paper_title}\" - {review_scores} - {'📜 ' * (number_real_messages)}"
                html_content += f"<details>\n<summary>{paper_summary}</summary>\n"

                paper_html = ""

                # Link to author feedback if PDF exists
                author_feedback_link = ""
                author_feedback_pdf_path = os.path.join(subfolder_path, 'AuthorFeedback.pdf')
                if os.path.isfile(author_feedback_pdf_path):
                    author_feedback_link = f" &middot; <a href='{author_feedback_pdf_path}' target='_blank'>Author Feedback</a>"

                # Add discussion messages
                if discussion_data:
                    paper_html += "  <div class='discussion'>\n"
                    paper_html += f"  <a href='https://cmt3.research.microsoft.com/{conference}/Discussion/Feed/{reviews_data[0]['SubmissionId']}'>Go to discussion</a>{author_feedback_link}\n"
                    for message in discussion_data:
                        author = message['FirstName'] if message['FirstName'] else message['Role']
                        date = message['Date'].split('T')[0]
                        time = message['Date'].split('T')[1].split('.')[0].split(':')[0] + ':' + message['Date'].split('T')[1].split('.')[0].split(':')[1]
                        text = message['Text']
                        if "The discussion is open now" in text:
                            continue
                        paper_html += f"    <div class='message'>\n"
                        paper_html += f"      <div class='author'>{author}</div>\n"
                        paper_html += f"      <div class='date'>{date} {time}</div>\n"
                        paper_html += f"      <div class='text'>{text}</div>\n"
                        paper_html += "    </div>\n"
                    # https://cmt3.research.microsoft.com/IJCAI2024/Discussion/Feed/2401
                    paper_html += "  </div>\n"

                # Loop through each review
                for review in reviews_data:
                    if not 'Questions' in review or not 'ReviewerNumber' in review:
                        continue
                    if len(review['Questions']) < 10:
                        reviewer_details = f"R{review['ReviewerNumber']}"
                    else:
                        reviewer_summary = review['Questions'][6]['Answers'][0]['Text'].split('.')[0]
                        confidence = review['Questions'][8]['Answers'][0]['Text'].split('.')[0]
                        knowledge = review['Questions'][9]['Answers'][0]['Text'].split(':')[0]
                        reviewer_summary += f" <span style='font-weight: normal'>/ {confidence} / {knowledge}</span>"
                        reviewer_details = f"R{review['ReviewerNumber']}: {reviewer_summary}"
                    paper_html += f"  <details>\n  <summary>{reviewer_details}</summary>\n  <ul>\n"
                    
                    # Loop through each question-answer pair for the current review
                    for question in review['Questions']:
                        if question['Order'] == 7 or question['Order'] == 9 or question['Order'] == 10 or question['Order'] == 12:
                            continue
                        if question['Order'] == 6 and "No" in question['Answers'][0]['Text']:
                            continue
                        if question['Order'] == 5 and ("CREDIBLE" in question['Answers'][0]['Text'] or "CONVINCING" in question['Answers'][0]['Text']):
                            continue

                        answer = question['Answers'][0]['Text'].replace('\n', '<br>')
                        if question['Order'] == 1:
                            answer = answer[:100] + "..." if len(answer) > 103 else answer

                        paper_html += f"    <li>{answer}</li>\n"
                        
                    paper_html += "  </ul>\n  </details>\n"

                html_content += paper_html
                html_content += "</details>\n"

    # Close the HTML content
    html_content += """
    </body>
    </html>
    """

    # Write the HTML content to a file
    output_file_path = 'reviews.html'
    with open(output_file_path, 'w') as file:
        file.write(html_content)

    print(f"HTML output saved to: {output_file_path}")

if __name__ == "__main__":
    if os.path.exists('last_conference.json'):
        with(open('last_conference.json')) as f:
            conference_file = json.load(f)
            conference = conference_file['conference_id']
    else:
        conference = input("Enter the conference ID: ")
    build_html(conference)
    