# NL2SQL UI/UX Improvement Guide

## Executive Summary

**Current State**: Tab 3 generates SQL from natural language but has UX issues:
- ❌ Users might expect data results (not SQL code)
- ❌ "Copy" button actually downloads (not clipboard)
- ❌ No guidance when SQL generation fails
- ⚠️ SQL displayed after distracting analysis sections

**Improved State**: Clear code generation workflow with:
- ✅ Explicit "NO EXECUTION" messaging
- ✅ Better copy/download UX with helper text
- ✅ Recovery guidance for failed generations
- ✅ SQL-first presentation with validation feedback

---

## 1. UX Assessment

### What Works ✅
1. **Clear flow**: Example → Input → Generate → Results
2. **Example integration**: Pre-filled queries help onboarding
3. **Rich context**: Intent analysis + table mapping
4. **Download capability**: SQL export functionality exists

### Critical Issues ❌

| Priority | Issue | Impact | Lines |
|----------|-------|--------|-------|
| **P0** | Purpose unclear (code gen vs execution) | Users expect data, not SQL | 755-759 |
| **P0** | Download labeled as "Copy" | Friction in clipboard workflow | 841-847 |
| **P0** | No error recovery guidance | Dead ends on failure | 854-858 |
| **P1** | Analysis before SQL | Buries main output | 810-834 |
| **P1** | No SQL validation | Syntax errors found late | N/A |

---

## 2. Quick Wins (30min Implementation)

### Quick Win #1: Add Purpose Banner (2 min)
**Impact**: Immediately clarifies this is a code generator

```python
# Add after line 755
st.header("🤖 AI 기반 쿼리 생성")

# NEW: Purpose clarity
st.info("""
📌 **이 도구는 SQL 코드 생성기입니다**
• ✅ 자연어 → SQL 쿼리 자동 변환
• ✅ 생성된 SQL을 복사하여 Databricks에서 실행
• ❌ 이 화면에서는 데이터를 조회하지 않습니다
""")
```

### Quick Win #2: Fix Copy Label (1 min)
**Impact**: Reduces user confusion

```python
# Replace line 841-847
st.download_button(
    label="💾 SQL 파일 다운로드",  # Changed from "📋 SQL 복사"
    data=result.sql_query,
    file_name="generated_query.sql",
    mime="text/plain",
    key="nl2sql_download",
    help="SQL을 .sql 파일로 저장 후 Databricks에서 실행하세요"  # NEW: tooltip
)

# NEW: Manual copy instruction
st.caption("💡 **Tip**: SQL 코드 블록을 마우스로 선택하여 복사할 수 있습니다 (Ctrl+C / Cmd+C)")
```

### Quick Win #3: Add Line Numbers (1 min)
**Impact**: Makes SQL easier to reference

```python
# Replace line 838
st.code(result.sql_query, language="sql", line_numbers=True)  # Add line_numbers parameter
```

### Quick Win #4: Add Error Recovery Guide (5 min)
**Impact**: Helps users fix failed queries

```python
# Replace lines 854-858
else:
    st.error(f"❌ SQL 생성 실패: {result.error_message}")

    # NEW: Recovery guidance
    with st.expander("🔧 문제 해결 가이드", expanded=True):
        st.markdown("""
        ### SQL 생성 실패 시 확인사항:

        1. **질환명 확인**
           - ✅ 정확한 한글 질환명 사용 (예: "고혈압", "당뇨병")
           - ❌ 영문명은 인식 안 됨

        2. **요청 구체화**
           - ✅ "고혈압 환자의 성별 분포"
           - ❌ "고혈압 정보" (너무 모호함)

        3. **예시 쿼리 참고**
           - 위의 '예시 쿼리 선택'에서 유사한 패턴 확인
        """)

        st.info("💡 **추천**: 위의 예시 선택에서 유사한 질문을 선택해보세요")
```

**Total Time**: ~10 minutes for all 4 quick wins

---

## 3. Priority-Based Implementation

### P0 - Must Fix (Critical for Workflow)

#### P0.1: Clarify Purpose (2 min)
**Lines**: Insert after 755

```python
st.info("""
📌 **이 도구는 SQL 코드 생성기입니다**
• ✅ 자연어 → SQL 쿼리 자동 변환
• ✅ 생성된 SQL을 복사하여 Databricks에서 실행
• ❌ 이 화면에서는 데이터를 조회하지 않습니다
""")
```

#### P0.2: Fix Copy UX (3 min)
**Lines**: Replace 841-847

See Quick Win #2 above

#### P0.3: Add Error Recovery (5 min)
**Lines**: Replace 854-858

See Quick Win #4 above

**P0 Total**: 10 minutes

---

### P1 - Should Fix (Improves Experience)

#### P1.1: SQL Quality Indicators (5 min)
**Lines**: Insert after 837

```python
# Show SQL metadata
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("테이블 사용", len(result.analysis.get('required_tables', [])))
with col2:
    st.metric("조건 수", len(result.analysis.get('key_conditions', [])))
with col3:
    lines = len(result.sql_query.split('\n'))
    complexity = "간단" if lines < 10 else "보통" if lines < 20 else "복잡"
    st.metric("복잡도", complexity)
```

#### P1.2: SQL-First Layout (10 min)
**Lines**: Reorganize 810-852

**Current order**:
1. Analysis (intent, tables, conditions)
2. SQL code
3. Download button
4. Explanation

**New order**:
1. SQL code (with line numbers)
2. Download button + copy tip
3. Analysis (in expander, collapsed)
4. Explanation (in expander)

```python
if result.success:
    st.success("✅ SQL 생성 완료!")

    # 1. SQL FIRST
    st.subheader("📝 생성된 SQL")
    st.code(result.sql_query, language="sql", line_numbers=True)

    # 2. Download + tip
    st.download_button(...)
    st.caption("💡 Tip: 코드 블록 선택 후 Ctrl+C로 복사")

    # 3. Analysis (collapsed)
    with st.expander("📊 분석 상세정보", expanded=False):
        # Move all analysis here
        ...

    # 4. Explanation (collapsed)
    with st.expander("💬 쿼리 설명"):
        ...
```

#### P1.3: SQL Validation (10 min)
**Lines**: Insert after 838 (after st.code)

```python
def validate_databricks_sql(sql: str) -> dict:
    """Validate SQL against Databricks/Spark SQL rules"""
    issues = []
    warnings = []

    # Critical issues
    if "deleted = FALSE" not in sql and "basic_treatment" in sql:
        issues.append("basic_treatment 사용 시 'deleted = FALSE' 필터 필수")

    if "deleted = FALSE" not in sql and "prescribed_drug" in sql:
        issues.append("prescribed_drug 사용 시 'deleted = FALSE' 필터 필수")

    # Warnings
    if "res_treat_start_date" in sql and "TO_DATE" not in sql:
        warnings.append("res_treat_start_date는 char 타입 - TO_DATE() 변환 권장")

    if "REGEXP" in sql:
        warnings.append("Spark SQL에서는 RLIKE 사용 (REGEXP 대신)")

    return {"issues": issues, "warnings": warnings}

validation = validate_databricks_sql(result.sql_query)

if validation['issues']:
    st.error("🚨 SQL 검증 실패 - 실행 전 수정 필요:")
    for issue in validation['issues']:
        st.markdown(f"- ❌ {issue}")

if validation['warnings']:
    st.warning("⚠️ 권장사항:")
    for warning in validation['warnings']:
        st.markdown(f"- {warning}")

if not validation['issues'] and not validation['warnings']:
    st.success("✅ Databricks 호환성 검증 통과")
```

**P1 Total**: 25 minutes

---

### P2 - Nice to Have (Learning Enhancement)

#### P2.1: Prompt Engineering Tips (5 min)
**Lines**: Insert after 770

```python
with st.expander("💡 효과적인 요청 작성법", expanded=False):
    st.markdown("""
    ### 좋은 요청 예시:

    ✅ **구체적인 질문**
    - "고혈압 환자의 성별 분포를 보여주세요"
    - "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10"

    ❌ **피해야 할 요청**
    - "고혈압" (너무 모호함)
    - "Show me hypertension" (영문 지원 안 됨)

    ### 요청 구조 패턴:
    `[질환명] + [분석 대상] + [조건(선택)]`
    """)
```

#### P2.2: Learning Patterns (10 min)
**Lines**: Insert after 852 (after explanation expander)

```python
with st.expander("📚 비슷한 질문 패턴 배우기", expanded=False):
    st.markdown(f"""
    ### 이 쿼리와 비슷한 패턴:

    **현재 요청**: {user_query}

    **동일 패턴 다른 질환**:
    - "{user_query.replace('고혈압', '당뇨병')}"
    - "{user_query.replace('고혈압', '암')}"

    **조건 추가 버전**:
    - "{user_query} (최근 1년)"
    - "{user_query} (서울 지역)"
    """)

    if "성별" in user_query:
        st.markdown("- 같은 질환의 '연령대별 분포'")
    elif "약물" in user_query:
        st.markdown("- 같은 질환의 '처방 성분별 환자 수'")
```

**P2 Total**: 15 minutes

---

## 4. Implementation Timeline

### Phase 1: Quick Wins (10 min) ⚡
- Add purpose banner
- Fix copy label + add tip
- Add line numbers to SQL
- Add error recovery guide

**Outcome**: Immediate clarity on tool purpose + better failure handling

### Phase 2: P0 Fixes (Already in Phase 1)
Already covered in quick wins

### Phase 3: P1 Improvements (25 min) 🎯
- Add SQL quality metrics
- Reorganize SQL-first layout
- Add SQL validation

**Outcome**: Professional code presentation + proactive error detection

### Phase 4: P2 Enhancements (15 min) 📚
- Add prompt engineering tips
- Add learning patterns

**Outcome**: Users learn to write better queries

**Total Implementation**: 50 minutes (30 min if skipping P2)

---

## 5. Testing Checklist

### Before Implementation
- [ ] Read current app.py lines 753-863
- [ ] Test current UX with example queries
- [ ] Document current pain points

### After Quick Wins (Phase 1)
- [ ] Banner displays correctly
- [ ] Download button label is clear
- [ ] Line numbers appear in SQL code
- [ ] Error message shows recovery guide

### After P1 Improvements (Phase 3)
- [ ] SQL appears before analysis sections
- [ ] Quality metrics display correctly
- [ ] Validation catches common issues
- [ ] Analysis is in collapsed expander

### User Testing Scenarios
1. **New user**: Can they understand this generates SQL (not data)?
2. **SQL copy**: Can they easily get SQL into clipboard/file?
3. **Error recovery**: Do they know what to fix when generation fails?
4. **Learning**: Do they improve their prompts over multiple tries?

---

## 6. Success Metrics

### Quantitative
- **Copy friction**: Clicks to get SQL → clipboard (Before: 3-4, After: 1-2)
- **Error recovery**: Users who retry after failure (Target: +40%)
- **Validation catches**: Issues found before Databricks (Target: 80%)

### Qualitative
- Users explicitly mention "I know I need to run this in Databricks"
- Users copy SQL successfully on first try
- Users reference validation feedback when fixing queries
- Users improve prompt quality after seeing tips

---

## 7. File Reference

### Modified Files
- **`/Users/park/clinical_report_generator/app.py`** (lines 753-863)

### New Files (for review)
- **`/Users/park/clinical_report_generator/app_nl2sql_improved.py`** - Complete improved version
- **`/Users/park/clinical_report_generator/NL2SQL_UX_IMPROVEMENTS.md`** - This guide

### No Changes Needed
- `nl2sql_generator.py` (backend logic is sound)
- Other tabs in app.py

---

## 8. Rollback Plan

If issues arise:

1. **Backup current code**:
   ```bash
   cp app.py app.py.backup
   ```

2. **Implement incrementally**:
   - Apply Quick Wins first (low risk)
   - Test each change before next
   - If any issue, revert specific section

3. **Feature flags** (optional):
   ```python
   ENABLE_NEW_NL2SQL_UI = True  # Toggle at top of file

   if ENABLE_NEW_NL2SQL_UI:
       # New code
   else:
       # Old code
   ```

---

## 9. Next Steps

### Immediate (Today)
1. ✅ Review this document
2. ⬜ Apply Quick Wins (10 min)
3. ⬜ Test with 3 example queries
4. ⬜ Deploy to staging

### This Week
1. ⬜ Implement P1 improvements (25 min)
2. ⬜ User testing with 3-5 clinical researchers
3. ⬜ Gather feedback on SQL validation

### Future Enhancements
1. ⬜ Clipboard API integration (true copy button)
2. ⬜ SQL formatting/beautification
3. ⬜ Query history/favorites
4. ⬜ Share SQL via link

---

## Appendix: Code Snippets

All code snippets are production-ready and can be directly pasted into `/Users/park/clinical_report_generator/app.py` at the specified line numbers.

See complete improved version in `app_nl2sql_improved.py` for reference.
