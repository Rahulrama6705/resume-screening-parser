import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from search_engine import SearchEngine


def show_model_accuracy():
    """Display model accuracy and performance metrics."""
    st.header("🎯 Model Accuracy & Performance Metrics")
    
    # Info box about auto-refresh
    st.info("💡 **Newly uploaded resumes in 'Process Resume' mode automatically appear here.** The accuracy metrics refresh in real-time.")
    
    search_engine = SearchEngine()
    candidates = search_engine.load_all_candidates()
    
    if not candidates:
        st.warning("No candidate data available. Process some resumes first.")
        return
    
    # Field completion analysis
    st.subheader("📊 Field Extraction Completeness")
    
    fields_to_analyze = ['name', 'email', 'phone', 'skills', 'experience', 'education', 'gpa', 'company']
    field_stats = {}
    
    for field in fields_to_analyze:
        filled = 0
        for candidate in candidates:
            value = candidate.get(field, '')
            if field == 'skills':
                if isinstance(value, list) and len(value) > 0:
                    filled += 1
            elif value and str(value).strip():
                filled += 1
        
        completion_rate = (filled / len(candidates)) * 100
        field_stats[field] = {
            'filled': filled,
            'total': len(candidates),
            'rate': completion_rate
        }
    
    # Display as table
    table_data = []
    for field, stats in field_stats.items():
        table_data.append({
            'Field': field.upper(),
            'Filled': stats['filled'],
            'Total': stats['total'],
            'Accuracy %': f"{stats['rate']:.1f}%"
        })
    
    df_accuracy = pd.DataFrame(table_data)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(df_accuracy, use_container_width=True)
    
    with col2:
        # Calculate average accuracy
        avg_accuracy = sum(s['rate'] for s in field_stats.values()) / len(field_stats)
        st.metric("Overall Extraction Accuracy", f"{avg_accuracy:.1f}%")
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart: Filled vs Empty
        filled_count = sum(s['filled'] for s in field_stats.values())
        empty_count = sum(s['total'] - s['filled'] for s in field_stats.values())
        
        ax1.pie([filled_count, empty_count], labels=['Extracted', 'Missing'], autopct='%1.1f%%',
               colors=['#2ecc71', '#e74c3c'], startangle=90)
        ax1.set_title('Data Extraction Status\n(All Fields Combined)')
        
        # Bar chart: Field-wise accuracy
        field_names = list(field_stats.keys())
        accuracy_rates = [field_stats[f]['rate'] for f in field_names]
        colors_map = ['#27ae60' if r >= 80 else '#f39c12' if r >= 50 else '#e74c3c' for r in accuracy_rates]
        
        ax2.barh(field_names, accuracy_rates, color=colors_map)
        ax2.set_xlabel('Completion Rate (%)')
        ax2.set_title('Field-wise Accuracy')
        ax2.set_xlim(0, 105)
        
        for i, v in enumerate(accuracy_rates):
            ax2.text(v + 1, i, f'{v:.0f}%', va='center')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # Detailed statistics
    st.subheader("📈 Detailed Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Resumes Processed", len(candidates))
    
    with col2:
        complete_candidates = sum(1 for c in candidates 
                                 if all(c.get(f, '') for f in ['name', 'email', 'experience']))
        st.metric("Complete Profiles", complete_candidates, 
                 f"{(complete_candidates/len(candidates)*100):.1f}%")
    
    with col3:
        avg_skills = sum(len(c.get('skills', [])) for c in candidates) / len(candidates)
        st.metric("Avg Skills Per Candidate", f"{avg_skills:.1f}")
    
    # Data quality breakdown
    st.subheader("🔍 Data Quality Breakdown (All Candidates)")
    
    quality_data = []
    for i, candidate in enumerate(candidates, 1):
        filled_fields = sum(1 for f in fields_to_analyze if candidate.get(f))
        quality_pct = (filled_fields / len(fields_to_analyze)) * 100
        quality_data.append({
            'Candidate': candidate.get('name', f'Candidate {i}')[:30],
            'Filled Fields': filled_fields,
            'Total Fields': len(fields_to_analyze),
            'Quality %': f"{quality_pct:.0f}%"
        })
    
    df_quality = pd.DataFrame(quality_data)
    st.dataframe(df_quality, use_container_width=True)
    
    st.caption(f"Showing all {len(candidates)} candidates | ✨ Newly uploaded resumes appear automatically")
