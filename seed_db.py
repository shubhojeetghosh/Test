"""
seed_db.py
==========
Populates the Neon PostgreSQL database with:
  - 1 exam  (EPS-TOPIK Practice Exam — Set 01)
  - 40 questions
  - 160 options (4 per question)
  - image rows for every question/option that has an image

Run from the project root:
    python seed_db.py

Safe to re-run — clears existing data for exam_id=1 before inserting.
"""

import os
import sys

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

from backend.quiz_engine.database import SessionLocal
from backend.quiz_engine.models import (
    ExamModel,
    ImageModel,
    OptionModel,
    QuestionModel,
)

# ── image URL prefix served by FastAPI StaticFiles ────────────────────────────
# When images are added back to backend/media/, they will be served at
# http://127.0.0.1:8000/media/<filename>.
# For now the URL is stored so the DB row is ready.
MEDIA = "/media/"


# ── question data ─────────────────────────────────────────────────────────────
# Each entry: (question_number, question_type, question_text, image_file, audio, options)
# options: list of (label, text, is_correct, option_image_file)
QUESTIONS = [
    # ── READING ──────────────────────────────────────────────────────────────
    (1,  "IMAGE",  "",
        "q1.jpg", False,
        [("A", "안경",  False, None),
         ("B", "가방",  False, None),
         ("C", "여권",  False, None),
         ("D", "지갑",  True,  None)]),

    (2,  "IMAGE",  "",
        "q2.jpg", False,
        [("A", "못을 박고 있습니다.",   False, None),
         ("B", "못을 조이고 있습니다.", False, None),
         ("C", "나사를 박고 있습니다.", False, None),
         ("D", "나사를 조이고 있습니다.", True, None)]),

    (3,  "READING", "다음 단어와 관계있는 것은 무엇입니까?\n칫솔, 비누, 샴푸, 수건",
        None, False,
        [("A", "세면도구", True,  None),
         ("B", "조리기구", False, None),
         ("C", "작업도구", False, None),
         ("D", "청소도구", False, None)]),

    (4,  "READING", "다음 단어와 비슷한 말은 무엇입니까?\n뽑다",
        None, False,
        [("A", "빼다", True,  None),
         ("B", "넣다", False, None),
         ("C", "놓다", False, None),
         ("D", "갈다", False, None)]),

    (5,  "READING", "도시는 사람이 너무 많아 시끄럽습니다. 하지만 시골은 ____이/가 적고 조용합니다.",
        None, False,
        [("A", "인구", True,  None),
         ("B", "유명", False, None),
         ("C", "통계", False, None),
         ("D", "교통", False, None)]),

    (6,  "READING", "_______ 에 한국에 왔습니다. 한국에 온지 벌써 1년이 됐습니다.",
        None, False,
        [("A", "작년",   True,  None),
         ("B", "내년",   False, None),
         ("C", "올해",   False, None),
         ("D", "재작년", False, None)]),

    (7,  "READING", "출퇴근 시간에는 버스보다 지하철이 ____ 빠릅니다. 도로에는 차가 많아서 복잡하기 때문입니다.",
        None, False,
        [("A", "더", True,  None),
         ("B", "잘", False, None),
         ("C", "참", False, None),
         ("D", "막", False, None)]),

    (8,  "READING", "가을에는 맛있는 ____이/가 많습니다. 저는 특히 사과와 배를 좋아합니다.",
        None, False,
        [("A", "과일", True,  None),
         ("B", "채소", False, None),
         ("C", "음료", False, None),
         ("D", "음식", False, None)]),

    (9,  "IMAGE", "이 표지는 무슨 뜻입니까?",
        "q9.jpg", False,
        [("A", "위로 올라가십시오.",     False, None),
         ("B", "왼쪽으로 가십시오.",     False, None),
         ("C", "똑바로 내려가십시오.",   False, None),
         ("D", "오른쪽으로 가십시오.",   True,  None)]),

    (10, "IMAGE", "이 사람이 하고 싶은 일은 무엇입니까?",
        "q10.jpg", False,
        [("A", "연락처입니다.",                     False, None),
         ("B", "이력서입니다.",                     True,  None),
         ("C", "오토캐드입니다.",                   False, None),
         ("D", "공일공 삼사오륙에 공일이삼입니다.", False, None)]),

    (11, "IMAGE", "다음 약 봉투에 대한 설명으로 맞는 것은 무엇입니까?",
        "q11.jpg", False,
        [("A", "사흘치 약입니다.",               False, None),
         ("B", "하루에 2번 복용해야 합니다.",    False, None),
         ("C", "약을 먹는 사람은 이상우입니다.", False, None),
         ("D", "식사를 한 후에 약을 먹습니다.",  True,  None)]),

    (12, "IMAGE", "산업별 외국인 취업자에 대한 설명으로 맞는 것은 무엇입니까?",
        "q12.jpg", False,
        [("A", "서비스업이 가장 많습니다.",      False, None),
         ("B", "제조업이 절반이 넘습니다.",      True,  None),
         ("C", "건설업이 두 번째로 많습니다.",   False, None),
         ("D", "농임업 보다 건설업이 더 많습니다.", False, None)]),

    (13, "READING", "한국 사람들은 설날에 떡국을 먹습니다. 나도 한국에서 오래 살아서 매년 설날이 되면 떡국을 _____.",
        None, False,
        [("A", "먹고 싶습니다", True,  None),
         ("B", "먹지 않습니다", False, None),
         ("C", "받고 싶습니다", False, None),
         ("D", "받지 않습니다", False, None)]),

    (14, "READING", "모니카씨, 감기에 걸렸네요. 감기 약을 먹으면 ________. 여기 감기약 드시고 푹 쉬세요.",
        None, False,
        [("A", "괜찮아 질 거예요", True,  None),
         ("B", "괜찮아 져도 돼요", False, None),
         ("C", "편찮아 질 거예요", False, None),
         ("D", "편찮아 져도 돼요", False, None)]),

    (15, "READING", "미영씨, 집들이 초대해줘서 고마워요. 너무 가고 싶지만 그 날은 고향에서 부모님이 오셔서 부모님과 함께 시간을 보내야 할 것 같아요. 다음에 기회 되면 식사 같이 해요.",
        None, False,
        [("A", "거절", True,  None),
         ("B", "약속", False, None),
         ("C", "부탁", False, None),
         ("D", "감사", False, None)]),

    (16, "READING", "작업장의 정리 정돈은 매우 중요합니다. 정리가 잘 되어 있는 작업장은 안전 사고 비율이 낮고 일의 집중력을 높여 근로자가 효율적으로 일할 수 있게 됩니다. 그 결과 작업 환경 개선과 회사의 생산성 발전의 효과까지 낳습니다.",
        None, False,
        [("A", "정리정돈 방법",      False, None),
         ("B", "작업자의 업무 효율", False, None),
         ("C", "안전 교육의 당위성", False, None),
         ("D", "정리정돈의 필요성",  True,  None)]),

    (17, "READING", "비빔밥은 한국 전통 음식 중의 하나입니다. 밥 위에 고기를 볶아서 놓고, 콩나물, 도라지, 버섯 등 여러 가지 나물도 예쁘게 놓고, 이것을 모두 섞어 비벼 먹는데, 한국 사람들은 보통 여기에 고추장을 넣어서 맵게 먹습니다.",
        None, False,
        [("A", "비빔밥은 최근에 생겨난 메뉴입니다.",          False, None),
         ("B", "비빔밥에는 나물이 한가지 종류만 있습니다.",   False, None),
         ("C", "비빔밥에는 된장을 넣습니다.",                 False, None),
         ("D", "한국사람은 비빔밥을 맵게 먹습니다.",          True,  None)]),

    (18, "READING", "한국에서는 보통 결혼식이 끝나면 폐백을 드립니다. 폐백은 신랑과 신부가 한복을 입고 신랑의 부모님과 친척들께 인사를 드리는 전통 풍습입니다. 폐백 때 신랑의 부모님은 신부에게 밤과 대추를 던져 줍니다. 여기에는 자식을 많이 낳고 행복하게 살라는 의미가 담겨 있습니다.",
        None, False,
        [("A", "폐백은 최근에 생겨난 결혼 풍습입니다.",              False, None),
         ("B", "폐백 때 신랑과 신부는 밤과 대추를 던집니다.",        False, None),
         ("C", "결혼식을 하기 전에 부모님께 폐백을 드립니다.",       False, None),
         ("D", "신랑의 친척들은 폐백에 참석해서 인사를 받습니다.",   True,  None)]),

    (19, "READING", "벼, 보리, 밀 등을 수확할 때 탈곡과 선별 작업을 동시에 할 수 있는 기계입니다.",
        None, False,
        [("A", "경운기", False, None),
         ("B", "콤바인", True,  None),
         ("C", "크레인", False, None),
         ("D", "불도저", False, None)]),

    (20, "READING", "법으로 정해 놓은 하루 근로 시간인 8시간이 넘게 일하는 것으로, 이 때 평소 수당의 1.5배를 지급합니다.",
        None, False,
        [("A", "연장 근로", True,  None),
         ("B", "야간 근로", False, None),
         ("C", "공제 총액", False, None),
         ("D", "세금 총액", False, None)]),

    # ── LISTENING ─────────────────────────────────────────────────────────────
    (21, "IMAGE_AUDIO", "다음을 듣고 들은 단어와 일치하는 것을 고르십시오.",
        "q21.jpg", True,
        [("A", "유리", False, None),
         ("B", "유로", False, None),
         ("C", "오리", True,  None),
         ("D", "오류", False, None)]),

    (22, "IMAGE_AUDIO", "다음을 듣고 들은 단어와 일치하는 것을 고르십시오.",
        "q22.jpg", True,
        [("A", "상처", False, None),
         ("B", "상추", True,  None),
         ("C", "상지", False, None),
         ("D", "상자", False, None)]),

    (23, "IMAGE_AUDIO", "다음을 듣고 알맞은 것을 고르십시오.",
        "q23.jpg", True,
        [("A", "공이 있어요.", True,  None),
         ("B", "공이 없어요.", False, None),
         ("C", "강이 있어요.", False, None),
         ("D", "강이 없어요.", False, None)]),

    (24, "IMAGE_AUDIO", "다음을 듣고 알맞은 것을 고르십시오.",
        "q24.jpg", True,
        [("A", "감을 줍고 있어요.", False, None),
         ("B", "공을 잡고 있어요.", False, None),
         ("C", "공을 줍고 있어요.", True,  None),
         ("D", "감을 잡고 있어요.", False, None)]),

    (25, "IMAGE_AUDIO", "이것은 무엇입니까?",
        "q25.jpg", True,
        [("A", "① 음성 선택지", True,  None),
         ("B", "② 음성 선택지", False, None),
         ("C", "③ 음성 선택지", False, None),
         ("D", "④ 음성 선택지", False, None)]),

    (26, "IMAGE_AUDIO", "여기는 어디입니까?",
        "q26.jpg", True,
        [("A", "① 음성 선택지", True,  None),
         ("B", "② 음성 선택지", False, None),
         ("C", "③ 음성 선택지", False, None),
         ("D", "④ 음성 선택지", False, None)]),

    (27, "IMAGE_AUDIO", "이 사람은 무엇을 하고 있습니까?",
        "q27.jpg", True,
        [("A", "① 음성 선택지", True,  None),
         ("B", "② 음성 선택지", False, None),
         ("C", "③ 음성 선택지", False, None),
         ("D", "④ 음성 선택지", False, None)]),

    (28, "IMAGE_AUDIO", "카메라가 얼마나 있습니까?",
        "q28.jpg", True,
        [("A", "① 음성 선택지", True,  None),
         ("B", "② 음성 선택지", False, None),
         ("C", "③ 음성 선택지", False, None),
         ("D", "④ 음성 선택지", False, None)]),

    (29, "IMAGE_AUDIO", "아파트는 어디에 있습니까?",
        "q29.jpg", True,
        [("A", "① 음성 선택지", True,  None),
         ("B", "② 음성 선택지", False, None),
         ("C", "③ 음성 선택지", False, None),
         ("D", "④ 음성 선택지", False, None)]),

    (30, "AUDIO_OPTION", "저기 가 우리 집이에요.",
        None, True,
        [("A", "저건 제 신발이에요.",         False, None),
         ("B", "필리핀으로 여행 가요.",        False, None),
         ("C", "우리 회사 반장님이에요.",      False, None),
         ("D", "음성으로 재생되는 선택지",     True,  None)]),

    (31, "AUDIO_OPTION", "다음 질문을 듣고 알맞은 대답을 고르십시오.",
        None, True,
        [("A", "네팔에 가요.",        False, None),
         ("B", "아침을 먹어요.",      False, None),
         ("C", "필리핀에서 왔어요.",  True,  None),
         ("D", "회사에서 일해요.",    False, None)]),

    (32, "AUDIO_OPTION", "다음 질문을 듣고 알맞은 대답을 고르십시오.",
        None, True,
        [("A", "네, 5분쯤 기다렸어요.",   False, None),
         ("B", "네, 잠깐만 기다리세요.",  True,  None),
         ("C", "네, 지금 빨리 가세요.",   False, None),
         ("D", "네, 다른 것을 보세요.",   False, None)]),

    (33, "AUDIO_OPTION", "다음 질문을 듣고 알맞은 대답을 고르십시오.",
        None, True,
        [("A", "구두를 신어요.",     False, None),
         ("B", "구보를 하고 있어요.", False, None),
         ("C", "친구를 기다려요.",   True,  None),
         ("D", "여기서 기다려요.",   False, None)]),

    (34, "AUDIO_OPTION", "실례지만 누구를 찾으세요.",
        None, True,
        [("A", "네. 잠깐만요.",             True,  None),
         ("B", "지금 통화 중이세요.",        False, None),
         ("C", "전화를 잘못 거셨어요.",      False, None),
         ("D", "실례지만 누구를 찾으세요.",  False, None)]),

    (35, "AUDIO_OPTION", "작업복 지퍼를 올리면 좀 답답해요.",
        None, True,
        [("A", "작업복으로 갈아 입어야겠어요.",      True,  None),
         ("B", "작업복 단추를 모두 잠글게요.",       False, None),
         ("C", "작업복을 어디뒀는지 모르겠어요.",    False, None),
         ("D", "작업복 지퍼를 올리면 좀 답답해요.", False, None)]),

    # Q36 — audio + 4 picture options
    (36, "IMAGE_AUDIO", "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오.",
        "q36.jpg", True,
        [("A", "① 그림", False, "q36-1.png"),
         ("B", "② 그림", False, "q36-2.png"),
         ("C", "③ 그림", True,  "q36-3.png"),
         ("D", "④ 그림", False, "q36-4.png")]),

    # Q37 — audio + 4 picture options
    (37, "IMAGE_AUDIO", "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오.",
        "q37.jpg", True,
        [("A", "① 그림", False, "q37-1.png"),
         ("B", "② 그림", False, "q37-2.png"),
         ("C", "③ 그림", False, "q37-3.png"),
         ("D", "④ 그림", True,  "q37-4.png")]),

    (38, "AUDIO_OPTION", "여자는 남자에게 왜 전화를 했습니까?",
        "q38.jpg", True,
        [("A", "부탁하려고", True,  None),
         ("B", "안내하려고", False, None),
         ("C", "조언하려고", False, None),
         ("D", "건의하려고", False, None)]),

    (39, "AUDIO_OPTION", "남자는 왜 휴가 날짜를 못 정했습니까?",
        "q39.jpg", True,
        [("A", "회사에 일이 많아서",      True,  None),
         ("B", "날짜가 많이 남아서",      False, None),
         ("C", "휴가를 가고 싶지 않아서", False, None),
         ("D", "휴가 신청을 하지 못해서", False, None)]),

    (40, "AUDIO_OPTION", "여자는 남자에게 왜 주의를 주고 있습니까?",
        "q40.jpg", True,
        [("A", "남자가 안전모를 안 쓰고 있어서",       False, None),
         ("B", "남자가 안전모를 분실해서",             False, None),
         ("C", "남자가 안전모를 잘못 쓰고 있어서",     True,  None),
         ("D", "남자가 안전모를 어떻게 쓰는지 몰라서", False, None)]),
]


# ── seed function ──────────────────────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        print("Connected to Neon PostgreSQL.")

        # ── clear existing data for exam id=1 to make seed idempotent ─────────
        existing_exam = db.query(ExamModel).filter_by(id=1).first()
        if existing_exam:
            print("Clearing existing data for exam id=1...")
            # cascade deletes handle questions → options → student_answers etc.
            db.query(QuestionModel).filter_by(exam_id=1).delete(synchronize_session=False)
            db.delete(existing_exam)
            db.commit()
            print("Cleared.")

        # ── insert exam ───────────────────────────────────────────────────────
        exam = ExamModel(
            title="EPS-TOPIK Practice Exam — Set 01",
            duration_minutes=50,
            total_questions=40,
            total_marks=100.0,
        )
        db.add(exam)
        db.flush()  # get exam.id
        print(f"Inserted exam id={exam.id}: {exam.title}")

        # ── insert questions + options + images ───────────────────────────────
        for (qnum, qtype, qtext, qimg, has_audio, opts) in QUESTIONS:
            # insert question-level image if present
            q_image_url = None
            if qimg:
                img_row = ImageModel(file_name=qimg, file_url=MEDIA + qimg)
                db.add(img_row)
                db.flush()
                q_image_url = img_row.file_url

            question = QuestionModel(
                exam_id=exam.id,
                question_number=qnum,
                question_type=qtype,
                question_text=qtext if qtext else None,
                image_url=q_image_url,
                audio_url=None,   # audio files not yet available
                marks=2.5,
                status="PUBLISHED",
            )
            db.add(question)
            db.flush()  # get question.id

            for (label, text, is_correct, opt_img) in opts:
                opt_image_url = None
                opt_image_id  = None
                if opt_img:
                    opt_img_row = ImageModel(file_name=opt_img, file_url=MEDIA + opt_img)
                    db.add(opt_img_row)
                    db.flush()
                    opt_image_url = opt_img_row.file_url
                    opt_image_id  = opt_img_row.id

                option = OptionModel(
                    question_id=question.id,
                    option_label=label,
                    option_text=text,
                    image_url=opt_image_url,
                    audio_url=None,
                    is_correct=is_correct,
                    image_id=opt_image_id,
                )
                db.add(option)

            print(f"  Q{qnum:02d} [{qtype:12s}] inserted  ({len(opts)} options)")

        db.commit()
        print(f"\nDone. Inserted 1 exam, 40 questions, 160 options.")

        # ── verify ────────────────────────────────────────────────────────────
        from sqlalchemy import text
        with db.bind.connect() as conn:
            eq = conn.execute(text("SELECT COUNT(*) FROM exams")).scalar()
            qq = conn.execute(text("SELECT COUNT(*) FROM questions")).scalar()
            oq = conn.execute(text("SELECT COUNT(*) FROM options")).scalar()
            iq = conn.execute(text("SELECT COUNT(*) FROM images")).scalar()
        print(f"Verification — exams:{eq}  questions:{qq}  options:{oq}  images:{iq}")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
