# NL2SQL UI Quick Wins - Ready-to-Apply Patches

**Implementation Time**: 10 minutes
**Impact**: 80% of UX improvement
**Risk**: Very low (UI-only changes)

---

## Instructions

1. Open `/Users/park/clinical_report_generator/app.py`
2. Apply each patch in sequence
3. Test with example queries
4. Deploy

---

## Patch 1: Add Purpose Banner (Line 755)

**Location**: After `st.header("🤖 AI 기반 쿼리 생성")`
**Time**: 1 minute

### Find this code (line 755-759):

```python
st.header("🤖 AI 기반 쿼리 생성")
st.markdown("""
자연어로 요청하면 스키마와 참조 데이터를 활용하여 SQL을 자동 생성합니다.
**레시피 없이** 자유로운 데이터 탐색이 가능합니다.
""")
```

### Replace with:

```python
st.header("🤖 AI 기반 쿼리 생성")

# NEW: Purpose clarity banner
st.info("""
📌 **이 도구는 SQL 코드 생성기입니다**
• ✅ 자연어 → SQL 쿼리 자동 변환
• ✅ 생성된 SQL을 복사하여 Databricks에서 실행
• ❌ 이 화면에서는 데이터를 조회하지 않습니다
""")

st.markdown("""
자연어로 요청하면 스키마와 참조 데이터를 활용하여 SQL을 자동 생성합니다.
**레시피 없이** 자유로운 데이터 탐색이 가능합니다.
""")
```

---

## Patch 2: Add Prompt Tips (Line 770)

**Location**: After `st.subheader("📝 자연어 요청")`
**Time**: 2 minutes

### Find this code (line 770-778):

```python
# User input
st.subheader("📝 자연어 요청")

# Example queries
example_queries = [
```

### Replace with:

```python
# User input
st.subheader("📝 자연어 요청")

# NEW: Prompt engineering help
with st.expander("💡 효과적인 요청 작성법", expanded=False):
    st.markdown("""
    ### 좋은 요청 예시:

    ✅ **구체적인 질문**
    - "고혈압 환자의 성별 분포를 보여주세요"
    - "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10"

    ✅ **조건 포함**
    - "서울 지역 3차 병원에서 치료받은 암 환자는 몇 명?"
    - "최근 1년간 고혈압으로 처방받은 약물 성분별 환자 수"

    ❌ **피해야 할 요청**
    - "고혈압" (너무 모호함)
    - "Show me hypertension patients" (영문 지원 안 됨)
    - "모든 정보 보여줘" (범위 불명확)

    ### 요청 구조 패턴:
    `[질환명] + [분석 대상] + [조건(선택)]`
    - 질환명: "고혈압", "당뇨병", "암"
    - 분석 대상: "환자 수", "성별 분포", "처방 약물"
    - 조건: "지역", "병원 등급", "기간"
    """)

# Example queries
example_queries = [
```

---

## Patch 3: Improve Placeholder Text (Line 791-797)

**Location**: Text area placeholder
**Time**: 1 minute

### Find this code (line 791-797):

```python
user_query = st.text_area(
    "무엇을 분석하고 싶으신가요?",
    value=default_query,
    height=100,
    placeholder="예: 고혈압 환자 중 남성과 여성의 비율은?",
    key="nl2sql_query_input"
)
```

### Replace with:

```python
user_query = st.text_area(
    "무엇을 분석하고 싶으신가요?",
    value=default_query,
    height=100,
    placeholder="예: 고혈압 환자 중 서울 지역 3차 병원에서 치료받은 환자의 연령대별 분포",
    help="구체적으로 작성할수록 정확한 SQL이 생성됩니다",
    key="nl2sql_query_input"
)
```

---

## Patch 4: Add Line Numbers to SQL (Line 838)

**Location**: SQL code display
**Time**: 1 minute

### Find this code (line 838):

```python
st.code(result.sql_query, language="sql")
```

### Replace with:

```python
st.code(result.sql_query, language="sql", line_numbers=True)
```

---

## Patch 5: Fix Download Button Label (Line 841-847)

**Location**: Download button
**Time**: 2 minutes

### Find this code (line 841-847):

```python
# Copy button
st.download_button(
    label="📋 SQL 복사",
    data=result.sql_query,
    file_name="generated_query.sql",
    mime="text/plain",
    key="nl2sql_download"
)
```

### Replace with:

```python
# Download button with clear label
st.download_button(
    label="💾 SQL 파일 다운로드",
    data=result.sql_query,
    file_name="generated_query.sql",
    mime="text/plain",
    key="nl2sql_download",
    help="SQL을 .sql 파일로 저장 후 Databricks에서 실행하세요"
)

# NEW: Manual copy instruction
st.caption("💡 **Tip**: SQL 코드 블록을 마우스로 선택하여 복사할 수 있습니다 (Ctrl+C / Cmd+C)")
```

---

## Patch 6: Add Error Recovery Guide (Line 854-858)

**Location**: Error handling
**Time**: 3 minutes

### Find this code (line 854-858):

```python
else:
    st.error(f"❌ SQL 생성 실패: {result.error_message}")

elif generate_button:
    st.warning("⚠️ 자연어 요청을 입력해주세요.")
```

### Replace with:

```python
else:
    st.error(f"❌ SQL 생성 실패: {result.error_message}")

    # NEW: Recovery guidance
    with st.expander("🔧 문제 해결 가이드", expanded=True):
        st.markdown("""
        ### SQL 생성 실패 시 확인사항:

        1. **질환명 확인**
           - ✅ 정확한 한글 질환명 사용 (예: "고혈압", "당뇨병")
           - ❌ 영문명은 인식 안 됨 (예: "hypertension" → "고혈압")

        2. **요청 구체화**
           - ✅ "고혈압 환자의 성별 분포"
           - ❌ "고혈압 정보" (너무 모호함)

        3. **테이블 제약 확인**
           - 사용 가능: basic_treatment, prescribed_drug, insured_person, hospital
           - 질환 필터: basic_treatment.res_disease_name
           - 약물 정보: prescribed_drug.res_drug_name

        4. **예시 쿼리 참고**
           - 위의 예시 선택 드롭다운에서 유사한 패턴 확인
        """)

        st.info("💡 **추천**: 위의 '예시 쿼리 선택'에서 유사한 질문을 선택해보세요")

elif generate_button:
    st.warning("⚠️ 자연어 요청을 입력해주세요.")
```

---

## Testing Checklist

After applying all patches:

### Visual Check
- [ ] Purpose banner appears at top (blue info box)
- [ ] Prompt tips available (collapsed expander)
- [ ] SQL shows line numbers
- [ ] Download button says "SQL 파일 다운로드"
- [ ] Copy tip appears below download button

### Functional Test
1. **Test Example Query**
   - [ ] Select "고혈압 환자의 성별 분포를 보여주세요"
   - [ ] Click "🚀 SQL 생성"
   - [ ] Verify SQL displays with line numbers
   - [ ] Verify download button works
   - [ ] Try selecting SQL and Ctrl+C

2. **Test Custom Query**
   - [ ] Enter "당뇨병 환자 수"
   - [ ] Click generate
   - [ ] Should succeed or show error with recovery guide

3. **Test Error Handling**
   - [ ] Enter gibberish or empty
   - [ ] Verify error message shows
   - [ ] Verify recovery guide expands automatically
   - [ ] Check if suggestions are helpful

4. **Test Prompt Tips**
   - [ ] Click "💡 효과적인 요청 작성법"
   - [ ] Verify examples display
   - [ ] Verify patterns are clear

---

## Before/After Screenshots

### Before
```
🤖 AI 기반 쿼리 생성
자연어로 요청하면...

📝 자연어 요청
[Textarea]
[🚀 SQL 생성]

✅ SQL 생성 완료!
📊 분석 결과...
📝 생성된 SQL
[Code block - no line numbers]
[📋 SQL 복사] ← Misleading!
```

### After
```
🤖 AI 기반 쿼리 생성
📌 이 도구는 SQL 코드 생성기입니다
• ✅ 자연어 → SQL 쿼리 자동 변환
• ✅ 생성된 SQL을 복사하여 Databricks에서 실행
• ❌ 이 화면에서는 데이터를 조회하지 않습니다

자연어로 요청하면...

📝 자연어 요청
💡 효과적인 요청 작성법 ▼
[Textarea with better placeholder]
💡 구체적으로 작성할수록...

[🚀 SQL 생성]

✅ SQL 생성 완료!
📝 생성된 SQL
[Code block WITH line numbers]
[💾 SQL 파일 다운로드]
💡 Tip: 코드 블록을 선택하여 복사...
```

---

## Rollback Plan

If any issue occurs:

### Quick Rollback
```bash
# Restore from backup
cp app.py.backup app.py
streamlit run app.py
```

### Partial Rollback
Remove specific patches by reversing:
- Patch 1: Remove info banner (lines 758-763)
- Patch 2: Remove expander (lines 773-793)
- Patch 3: Revert placeholder text
- Patch 4: Remove `line_numbers=True`
- Patch 5: Revert button label
- Patch 6: Remove expander (lines 857-878)

---

## Validation

After applying all patches, verify:

```python
# Count of changes
# - Added: ~40 lines
# - Modified: ~5 lines
# - Removed: 0 lines
# - Total diff: ~45 lines

# Files modified
# - app.py only

# Dependencies added
# - None (uses existing Streamlit features)

# Breaking changes
# - None (all additive)
```

---

## Expected User Feedback

### Positive Signals
- "Oh, I see - this generates SQL code, not data"
- "Line numbers make it easier to reference"
- "The error guide helped me fix my query"
- "The tips helped me write better prompts"

### Risk Signals (if any)
- "Too much text" → Collapse tips by default
- "Still confusing" → Enhance banner
- "Copy still hard" → Consider clipboard API

---

## Next Steps After Quick Wins

If quick wins are successful:

1. **Measure Impact** (1 week)
   - User confusion rate
   - Error recovery success
   - Query quality improvement

2. **Implement P1** (25 min)
   - SQL validation
   - Quality metrics
   - Layout reorganization

3. **Implement P2** (15 min)
   - Learning patterns
   - Enhanced tips

See `NL2SQL_UX_IMPROVEMENTS.md` for full roadmap.

---

## Support

If issues arise:
1. Check Streamlit version: `streamlit --version` (should be 1.x)
2. Test in clean session: `streamlit run app.py --server.runOnSave true`
3. Review error logs: Check terminal output
4. Compare with: `app_nl2sql_improved.py` (reference implementation)

Contact: Review code changes in this directory
- `NL2SQL_UX_IMPROVEMENTS.md` - Full guide
- `NL2SQL_BEFORE_AFTER.md` - Visual comparison
- `app_nl2sql_improved.py` - Complete improved version
